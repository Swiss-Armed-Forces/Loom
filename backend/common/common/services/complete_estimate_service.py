import logging
import time

from pydantic import BaseModel
from redis import StrictRedis

from common.celery_app import TaskGroupName
from common.file.file_repository import FileRepository
from common.services.celery_inspect_service import CeleryInspectService
from common.services.query_builder import QueryParameters
from common.services.queues_service import QueuesService
from common.settings import CELERY_QUEUE_NAME_MAXLEN, settings

logger = logging.getLogger(__name__)

_REDIS_KEY_PREFIX = "complete_estimate"
_KEY_FILES_PENDING = f"{_REDIS_KEY_PREFIX}:files_pending"
_KEY_LAST_TIMESTAMP = f"{_REDIS_KEY_PREFIX}:last_timestamp"
_KEY_EMA_THROUGHPUT = f"{_REDIS_KEY_PREFIX}:ema_throughput"
_KEY_ESTIMATE_TS = f"{_REDIS_KEY_PREFIX}:estimate_ts"

# Smoothing factor for the exponential moving average of throughput (files/s).
# Higher values weight recent observations more heavily (more reactive),
# lower values produce a smoother but slower-adapting estimate.
EMA_ALPHA = 0.3

# Minimum throughput (files/s) required to emit an estimate.
# Below this threshold the EMA has decayed so close to zero (due to stalls or
# a growing backlog) that dividing pending/ema would produce astronomically large
# and meaningless timestamps.  1 file/hour is already an extremely slow pace;
# anything slower than that is treated as "can't estimate".
_MIN_EMA_THROUGHPUT = 1.0 / 3600


class CompleteEstimateResult(BaseModel):
    estimate_timestamp: int | None
    files_pending: int | None


class CompleteEstimateService:
    def __init__(
        self,
        redis_client: StrictRedis,
        queues_service: QueuesService,
        celery_inspect_service: CeleryInspectService,
        file_repository: FileRepository,
    ):
        self._redis = redis_client
        self._queues_service = queues_service
        self._celery_inspect_service = celery_inspect_service
        self._file_repository = file_repository

    def _get_pending_work(self) -> int:
        """Return combined pending work: dispatch queue depth + ES non-terminal files.

        Files flow from dispatch queues (before ES) → ES non-terminal states →
        processed. These two buckets are non-overlapping, so their sum is the total work
        remaining.
        """
        dispatch_names = self._celery_inspect_service.get_task_names_in_group(
            TaskGroupName.DISPATCH
        )
        all_counts = self._queues_service.get_all_queue_message_counts()
        prefix = settings.celery_queue_name_prefix
        dispatch_depth = sum(
            all_counts.get(f"{prefix}{name}"[:CELERY_QUEUE_NAME_MAXLEN], 0)
            for name in dispatch_names
        )

        es_pending = self._file_repository.count_by_query(
            QueryParameters(
                query_id=self._file_repository.open_point_in_time(),
                search_string=(
                    f'NOT state:("processed" OR "failed")'
                    f" AND reindex_count:<{settings.max_reindex_count}"
                ),
            )
        )

        return dispatch_depth + es_pending

    def compute_and_store(self) -> None:
        """Compute pending work, update EMA throughput, and cache the estimate in Redis.

        Called by the periodic beat task every minute.
        """
        now = time.time()
        current_pending = self._get_pending_work()

        pipe = self._redis.pipeline()
        pipe.get(_KEY_FILES_PENDING)
        pipe.get(_KEY_LAST_TIMESTAMP)
        pipe.get(_KEY_EMA_THROUGHPUT)
        _lp, _lt, _pe = pipe.execute()
        last_pending: int | None = int(_lp) if _lp is not None else None
        last_ts: float | None = float(_lt) if _lt is not None else None
        prev_ema: float | None = float(_pe) if _pe is not None else None

        new_ema: float | None = None
        if last_pending is not None and last_ts is not None:
            elapsed = now - last_ts
            if elapsed > 0:
                current_rate = (last_pending - current_pending) / elapsed
                if prev_ema is not None:
                    new_ema = EMA_ALPHA * current_rate + (1 - EMA_ALPHA) * prev_ema
                else:
                    new_ema = current_rate

        estimate_ts: int | None = None
        if (
            new_ema is not None
            and new_ema >= _MIN_EMA_THROUGHPUT
            and current_pending > 0
        ):
            estimate_ts = int(now + current_pending / new_ema)

        self._redis.set(_KEY_FILES_PENDING, current_pending)
        self._redis.set(_KEY_LAST_TIMESTAMP, now)
        if current_pending == 0:
            self._redis.delete(_KEY_EMA_THROUGHPUT)
        elif new_ema is not None:
            self._redis.set(_KEY_EMA_THROUGHPUT, max(0.0, new_ema))
        if estimate_ts is not None:
            self._redis.set(_KEY_ESTIMATE_TS, estimate_ts)
        else:
            self._redis.delete(_KEY_ESTIMATE_TS)

        logger.debug(
            "Complete estimate: pending=%d, ema_throughput=%.4f files/s, estimate_ts=%s",
            current_pending,
            new_ema if new_ema is not None else 0.0,
            estimate_ts,
        )

    def get_cached_result(self) -> CompleteEstimateResult:
        """Return the last cached estimate and files_pending count from Redis."""
        _et = self._redis.get(_KEY_ESTIMATE_TS)
        _fp = self._redis.get(_KEY_FILES_PENDING)
        estimate_ts = int(_et) if _et is not None else None
        if estimate_ts is not None and estimate_ts < int(time.time()):
            estimate_ts = None
        return CompleteEstimateResult(
            estimate_timestamp=estimate_ts,
            files_pending=int(_fp) if _fp is not None else None,
        )
