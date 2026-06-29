import logging

from celery import chord
from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
    get_lazybytes_service,
)
from common.services.lazybytes_service import TempLazyBytesService
from common.settings import settings
from common.utils.task_lock import task_lock

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import (
    flush_cache,
    flush_lazybytes,
)

logger = logging.getLogger(__name__)

app = get_celery_app()

_THROTTLE_AND_FLUSH_LAZYBYTES_LOCK_TTL_SECONDS = 60 * 15  # 15 minutes
_WAIT_FOR_IDLE_TIMEOUT_SECONDS = 60 * 10  # 10 minutes (well under lock TTL)
_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS = 10.0


def _should_throttle(lazybytes_service: TempLazyBytesService) -> bool:
    """Return True if temp lazybytes usage exceeds the configured threshold."""
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
@task_lock(ttl_seconds=_THROTTLE_AND_FLUSH_LAZYBYTES_LOCK_TTL_SECONDS, blocking=False)
def throttle_and_flush_lazybytes_task(self: PeriodicTask):
    """Manage lazybytes cleanup and throttling under resource pressure.

    Only acts when temp lazybytes usage exceeds the configured threshold. When
    triggered, pauses DISPATCH tasks (via set_throttled) so no new file ingestion
    pipelines start, then waits for all non-throttled queues to drain before flushing
    lazybytes and cache.

    If the idle wait times out, DISPATCH remains paused until the next run succeeds and
    flush_complete resumes it. Files are safe in file_storage_service, so queued tasks
    can resume processing after throttling ends.
    """
    inspect = get_celery_inspect_service()
    if not _should_throttle(get_lazybytes_service()):
        if inspect.is_throttled():
            inspect.set_throttled(False)
            logger.info("Below threshold: resuming")
        return None

    inspect.set_throttled(True)

    exclude_tasks = inspect.get_throttled_tasks() + [self.name]
    if not inspect.wait_for_idle(
        timeout=_WAIT_FOR_IDLE_TIMEOUT_SECONDS,
        poll_interval=_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS,
        exclude_tasks=exclude_tasks,
    ):
        logger.info("Celery not idle: timed out waiting for idle")
        return None

    logger.info("Celery idle: flushing")
    return self.replace(
        chord(
            [
                flush_cache.signature(),
                flush_lazybytes.signature(),
            ],
            flush_complete.s(),
        )
    )
