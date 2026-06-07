import logging

from celery import chord
from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
    get_lazybytes_service,
    get_root_task_information_repository,
)
from common.services.lazybytes_service import TempLazyBytesService
from common.settings import settings
from common.task_object.root_task_information_repository import (
    RootTaskInformationRepository,
)
from common.utils.task_lock import task_lock

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import (
    flush_cache,
    flush_lazybytes,
    flush_root_task_information,
)

logger = logging.getLogger(__name__)

app = get_celery_app()

_FLUSH_ON_IDLE_LOCK_TTL_SECONDS = 60 * 15  # 15 minutes
_WAIT_FOR_IDLE_TIMEOUT_SECONDS = 60 * 10  # 10 minutes (well under lock TTL)
_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS = 10.0


def _should_throttle(
    lazybytes_service: TempLazyBytesService,
    root_task_information_repository: RootTaskInformationRepository,
) -> bool:
    """Check if indexing should be throttled based on resource accumulation."""
    # Check the fast Elasticsearch count first to avoid the expensive S3 scan
    # when the root task limit alone is sufficient to trigger throttling.
    root_task_count = root_task_information_repository.count()
    if root_task_count >= settings.throttle_max_root_tasks:
        logger.info(
            "Throttling: root task count %d >= %d",
            root_task_count,
            settings.throttle_max_root_tasks,
        )
        return True
    lazybytes_total_size_bytes = lazybytes_service.get_total_size_bytes()
    if lazybytes_total_size_bytes >= settings.throttle_max_lazybytes__bytes:
        logger.info(
            "Throttling: lazybytes usage %d GiB >= %d GiB",
            lazybytes_total_size_bytes // (1024**3),
            settings.throttle_max_lazybytes__bytes // (1024**3),
        )
        return True
    return False


@app.task(base=PeriodicTask)
def flush_complete(*_, **__):
    get_celery_inspect_service().set_throttled(False)
    logger.info("Flushing complete")


@app.task(bind=True, base=PeriodicTask)
@task_lock(ttl_seconds=_FLUSH_ON_IDLE_LOCK_TTL_SECONDS, blocking=False)
def flush_on_idle_task(self: PeriodicTask):
    """Manage lazybytes cleanup and throttling.

    When lazybytes accumulates beyond the threshold, this task throttles
    the system by cancelling dispatch consumers. This allows:
    1. Currently active tasks to complete
    2. System to become idle (excluding throttled tasks)
    3. This task to clean up intermediate lazybytes
    4. Throttle to be lifted after lazybytes pressure is reduced

    Files are safe in file_storage_service, so queued tasks can resume
    processing after throttling ends.
    """
    lazybytes_service = get_lazybytes_service()
    root_task_information_repository = get_root_task_information_repository()
    should_throttle = _should_throttle(
        lazybytes_service, root_task_information_repository
    )

    inspect = get_celery_inspect_service()

    if should_throttle:
        # Throttle: set system flag and pause dispatch consumers
        inspect.set_throttled(True)

    # Wait for idle EXCLUDING dispatch tasks (they are throttled while flushing)
    if not inspect.wait_for_idle(
        timeout=_WAIT_FOR_IDLE_TIMEOUT_SECONDS,
        poll_interval=_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS,
        called_from_task=True,
        exclude_tasks=inspect.get_throttled_tasks(),
    ):
        logger.info("Celery not idle: timed out waiting for idle")
        return None

    logger.info("Celery idle: flushing")
    return self.replace(
        chord(
            [
                flush_cache.signature(),
                flush_lazybytes.signature(),
                flush_root_task_information.signature(),
            ],
            flush_complete.s(),
        )
    )
