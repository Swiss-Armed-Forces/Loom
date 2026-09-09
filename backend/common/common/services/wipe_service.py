import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from time import monotonic, sleep

from celery import Celery
from elasticsearch import Elasticsearch
from minio import Minio
from redis import StrictRedis

from common.celery_app import BaseTask
from common.messages.pubsub_service import PubSubService
from common.models.es_repository import ES_REPOSITORY_TYPES
from common.services.celery_inspect_service import CeleryInspectService
from common.services.imap_service import IMAPService
from common.services.lazybytes_service import LazyBytesService
from common.services.query_builder import QueryBuilder
from common.services.queues_service import QueuesService
from common.settings import settings
from common.utils.flush_s3_bucket import flush_s3_bucket

logger = logging.getLogger(__name__)

WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S = 0.1
WIPE_CELERY_TIMEOUT__S = 300.0
# Upper bound on concurrent queue purges. wipe_celery() re-purges every 0.1s, so this
# caps how many requests a single wipe can have in flight against the broker.
PURGE_MAX_WORKERS = 16


class WipeTimeoutError(RuntimeError):
    """Raised when celery did not go idle within the wipe timeout."""


class WipeService:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        celery_app: "Celery[BaseTask]",
        elasticsearch: Elasticsearch,
        query_builder: QueryBuilder,
        pubsub_service: PubSubService,
        redis_client: StrictRedis,
        redis_cache_client: StrictRedis,
        s3_intake_client: Minio,
        file_storage_service: LazyBytesService,
        lazybytes_service: LazyBytesService,
        imap_service: IMAPService,
        celery_inspect_service: CeleryInspectService,
        queues_service: QueuesService,
    ):
        self._celery_app = celery_app
        self._elasticsearch = elasticsearch
        self._query_builder = query_builder
        self._pubsub_service = pubsub_service
        self._redis_client = redis_client
        self._redis_cache_client = redis_cache_client
        self._s3_intake_client = s3_intake_client
        self._file_storage_service = file_storage_service
        self._lazybytes_service = lazybytes_service
        self._imap_service = imap_service
        self._celery_inspect_service = celery_inspect_service
        self._queues_service = queues_service

    def wipe_celery(self, timeout__s: float = WIPE_CELERY_TIMEOUT__S) -> None:
        logger.info("Wiping: celery")
        celery_control = self._celery_app.control
        deadline = monotonic() + timeout__s
        while True:
            # Purge on every iteration, not just once up front: tasks that are already
            # in flight publish their successors as they complete, so a single purge
            # drains nothing durably.
            self.wipe_rabbit()
            # send termination signal for all remaining tasks
            # these are most likely tasks which are backing off
            # at the workers.
            for task in self._celery_inspect_service.iterate_tasks():
                task_id = task.get("id", None)
                if isinstance(task_id, str):
                    logger.info("Terminating task: %s", task_id)
                    celery_control.terminate(task_id)
            if self._celery_inspect_service.is_idle():
                return
            if monotonic() >= deadline:
                raise WipeTimeoutError(
                    f"Celery did not go idle within {timeout__s}s; "
                    f"{self._queues_service.get_message_count()} messages remain"
                )
            sleep(WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S)

    def wipe_elasticsearch(self) -> None:
        logger.info("Wiping: elasticsearch")

        def set_destructive_requires_name(required: bool):
            self._elasticsearch.cluster.put_settings(
                transient={"action": {"destructive_requires_name": required}}
            )

        @contextmanager
        def allow_destructive_without_name():
            set_destructive_requires_name(False)
            try:
                yield
            finally:
                set_destructive_requires_name(True)

        with allow_destructive_without_name():
            self._elasticsearch.indices.delete(index="*")

        for repository_type in ES_REPOSITORY_TYPES:
            repository_type(
                query_builder=self._query_builder, pubsub_service=self._pubsub_service
            ).init()

        # Using this would be faster, but doesn't fully work :(
        # self._elasticsearch.delete_by_query(index="*", body={"query": {"match_all": {}}})

    def wipe_redis(self) -> None:
        logger.info("Wiping: redis")
        self._redis_client.flushall()
        self._redis_cache_client.flushall()

    def wipe_intake(self) -> None:
        logger.info("Wiping: intake")
        bucket_name = settings.intake_storage.bucket_name
        logger.info("Clearing bucket: %s", bucket_name)
        flush_s3_bucket(self._s3_intake_client, bucket_name)

    def wipe_file_storage(self) -> None:
        logger.info("Wiping: file storage service")
        self._file_storage_service.flush()

    def wipe_lazybytes(self) -> None:
        logger.info("Wiping: lazybytes service")
        self._lazybytes_service.flush()

    def wipe_imap(self) -> None:
        logger.info("Wiping: IMAP")
        self._imap_service.wipe()

    def wipe_rabbit(self) -> None:
        """Purge every queue the broker names, regardless of its reported depth.

        ``celery_control.purge()`` must not be used here. It purges
        ``app.amqp.queues.consume_from``, built from ``app.conf.task_queues``, which
        only ``register_tasks_for_package()`` populates — and only worker processes call
        that. In the API process that list holds nothing but the static queues (default,
        graveyard, dead, abyss), so the per-task queues would never be purged. Asking
        the broker instead works from any process, because the broker knows every queue
        that exists.

        Covers the terminal queues (abyss, unroutable) that no worker consumes, and the
        ``celery_delayed_*`` queues holding tasks in a retry backoff.

        The reported depths name the queues but must not decide which ones to purge: the
        management API serves them from its stats database, refreshed only every
        ``collect_statistics_interval`` (10s), and reports no ``messages`` column at all
        for a queue it has not sampled yet. A queue holding a just-published backlog
        therefore reads as empty, and skipping it would let a wipe return having purged
        nothing. Purging an already-empty queue costs one request and is harmless.
        """
        queue_names = [
            *self._queues_service.get_all_queue_message_counts(),
            *self._queues_service.get_delayed_queue_message_counts(),
        ]
        if not queue_names:
            return
        logger.info("Purging %d queues", len(queue_names))
        # The purges are independent HTTP round-trips against the broker; run them
        # concurrently so a wipe does not serialize dozens of them.
        with ThreadPoolExecutor(
            max_workers=min(len(queue_names), PURGE_MAX_WORKERS)
        ) as executor:
            futures = [
                executor.submit(self._queues_service.purge_queue, queue_name)
                for queue_name in queue_names
            ]
            for future in futures:
                # Surface the first failure — a purge that silently did not happen
                # would let wipe_celery() loop until its timeout with no explanation.
                future.result()
