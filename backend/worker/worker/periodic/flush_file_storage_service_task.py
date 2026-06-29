import logging
import uuid
from datetime import datetime, timedelta, timezone
from itertools import islice

from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
    get_file_storage_service,
)
from common.utils.task_lock import task_lock

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks.flush_file_storage_service import (
    search_and_remove_file_storage_object,
)
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()

_FLUSH_FILE_STORAGE_SERVICE_LOCK_TTL_SECONDS = 60 * 15  # 15 minutes
_WAIT_FOR_IDLE_TIMEOUT_SECONDS = 60 * 10  # 10 minutes (well under lock TTL)
_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS = 10.0
_MIN_AGE = timedelta(days=1)


@app.task(bind=True, base=PeriodicTask)
@task_lock(ttl_seconds=_FLUSH_FILE_STORAGE_SERVICE_LOCK_TTL_SECONDS, blocking=False)
def flush_file_storage_service_task(
    self: PeriodicTask,
    min_age_seconds: float | None = None,
    start_after_service_id: str | None = None,
):
    min_age = (
        timedelta(seconds=min_age_seconds) if min_age_seconds is not None else _MIN_AGE
    )
    logger.info("Flushing file storage service")
    inspect = get_celery_inspect_service()
    if not inspect.wait_for_idle(
        timeout=_WAIT_FOR_IDLE_TIMEOUT_SECONDS,
        poll_interval=_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS,
        exclude_tasks=[self.name],
    ):
        logger.info("Celery not idle: timed out waiting for idle, skipping flush")
        return
    # Use a random UUID as the start point so each run covers a different slice of the
    # bucket, providing uniform coverage over time without a fixed iteration order.
    # An explicit start_after_service_id can be passed to override this (e.g. "" for
    # a full scan in tests).
    if start_after_service_id is None:
        start_after_service_id = str(uuid.uuid4())
    logger.debug(
        "Iterating file storage service starting after %s", start_after_service_id
    )
    cutoff = datetime.now(timezone.utc) - min_age
    all_objects = get_file_storage_service().iterate(
        start_after_service_id=start_after_service_id
    )
    old_objects = (
        lb
        for lb in all_objects
        if lb.last_modified is not None and lb.last_modified < cutoff
    )
    for lazy_bytes in islice(
        old_objects, settings.flush_file_storage_service_max_objects
    ):
        logger.debug("Dispatching search_and_remove for %s", lazy_bytes.service_id)
        search_and_remove_file_storage_object.s(
            service_id=str(lazy_bytes.service_id)
        ).delay().forget()
