import logging

from celery import chain, group
from common.dependencies import get_celery_app
from common.file.file_repository import File
from common.services.lazybytes_service import TempLazyBytes
from common.services.task_scheduling_service import IndexingPriority

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import (
    create_thumbnail,
    persist_processing_done,
    render,
    tika_processing,
)

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def index_file_task(
    file: File,
    file_content: TempLazyBytes,
    max_recursion_depth: int,
    priority: IndexingPriority = IndexingPriority.MEDIUM,
):
    logger.info("Indexing file with id '%s'", file.id_)

    # The whole per-file fan-out carries the priority, not just the message that
    # starts it: the tika and render queues are where contention shows up as
    # interactive latency.
    chain(
        group(
            create_thumbnail.signature(file, file_content),
            render.signature(file, file_content),
            tika_processing.signature(
                file_content, file, max_recursion_depth, priority
            ),
        ),
        persist_processing_done.signature(file.id_),
    ).apply_async(priority=priority).forget()
