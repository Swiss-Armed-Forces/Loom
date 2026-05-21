import logging

from celery import chain, group
from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
    get_lazybytes_service,
    get_root_task_information_repository,
)
from common.services.lazybytes_service import TempLazyBytesService
from common.settings import CELERY_QUEUE_NAME_MAXLEN, settings
from common.task_object.root_task_information_repository import (
    RootTaskInformationRepository,
)

from worker.index_file.index_file_task import dispatch_index_file
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import (
    flush_cache,
    flush_lazybytes,
    flush_root_task_information,
)

logger = logging.getLogger(__name__)

app = get_celery_app()


def _get_dispatch_index_file_queue() -> str:
    return (f"{settings.celery_queue_name_prefix}{dispatch_index_file.name}")[
        :CELERY_QUEUE_NAME_MAXLEN
    ]


def _should_throttle(
    lazybytes_service: TempLazyBytesService,
    root_task_information_repository: RootTaskInformationRepository,
) -> bool:
    """Check if indexing should be throttled based on resource accumulation."""
    lazybytes_total_size_bytes = lazybytes_service.get_total_size_bytes()
    if lazybytes_total_size_bytes >= settings.throttle_max_lazybytes__bytes:
        logger.info(
            "Throttling: lazybytes usage %d GiB >= %d GiB",
            lazybytes_total_size_bytes // (1024**3),
            settings.throttle_max_lazybytes__bytes // (1024**3),
        )
        return True
    root_task_count = root_task_information_repository.count()
    if root_task_count >= settings.throttle_max_root_tasks:
        logger.info(
            "Throttling: root task count %d >= %d",
            root_task_count,
            settings.throttle_max_root_tasks,
        )
        return True
    return False


def pause_index_file_queue(pause: bool = True):
    queue = _get_dispatch_index_file_queue()
    celery_app = get_celery_app()
    if pause:
        result = celery_app.control.cancel_consumer(
            queue,
            reply=True,
        )
    else:
        result = celery_app.control.add_consumer(
            queue,
            reply=True,
        )
    logger.info(
        "%s: index_file queue, result=%s", "Pause" if pause else "Resume", result
    )


@app.task(base=PeriodicTask)
def flush_complete(*_, **__):
    pause_index_file_queue(pause=False)
    logger.info("Flushing complete")


@app.task(bind=True, base=PeriodicTask)
def flush_on_idle_task(self: PeriodicTask):
    """Manage lazybytes cleanup and queue throttling.

    When lazybytes accumulates beyond the threshold, this task pauses
    the index_file queue by cancelling consumers. This allows:
    1. Currently active tasks to complete
    2. System to become idle (excluding the paused queue)
    3. This task to clean up intermediate lazybytes
    4. Queue to resume after lazybytes pressure is reduced

    Files are safe in file_storage_service, so queued tasks can resume
    processing after the pause.
    """
    lazybytes_service = get_lazybytes_service()
    root_task_information_repository = get_root_task_information_repository()
    throttling = _should_throttle(lazybytes_service, root_task_information_repository)

    if throttling:
        # Pause: tell all workers to stop consuming from index_file queue
        pause_index_file_queue(pause=True)

    # Check idle EXCLUDING the throttled queue
    if get_celery_inspect_service().is_idle(
        called_from_task=True, exclude_queues=[_get_dispatch_index_file_queue()]
    ):
        logger.info("Celery idle: flushing")
        return self.replace(
            chain(
                group(
                    flush_cache.signature(),
                    flush_lazybytes.signature(),
                    flush_root_task_information.signature(),
                ),
                flush_complete.s(),
            )
        )
    return None
