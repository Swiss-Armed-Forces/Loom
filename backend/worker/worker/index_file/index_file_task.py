"""Taks that starts the indexing pipeline."""

import logging
from uuid import UUID

from celery import chain, group
from common.celery_app import CELERY_QUEUE_MIN_PRIORITY
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_scheduling_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks import (
    create_thumbnail,
    extract_loom_archive,
    extract_magic_file_type,
    persist_processing_done,
    tika_processing,
)

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task()
def dispatch_reindex_files(query: QueryParameters):
    logger.info("Dispatching tasks to reindex files with query '%s'", query)
    for file in get_file_repository().get_id_generator_by_query(query=query):
        dispatch_reindex_file.s(file_id=file.id_).delay().forget()


@app.task()
def dispatch_reindex_file(file_id: UUID):
    logger.info("Dispatching tasks to reindex files with id '%s'", file_id)
    get_file_scheduling_service().reindex_file(file_id=file_id)


# Note: set priority here to the lowest possible, this is to prevent
# loom from indexing new files when there are old files
# still in beeing indexed.
@app.task(base=FileIndexingTask, priority=CELERY_QUEUE_MIN_PRIORITY)
def index_file_task(file: File, file_content: LazyBytes):
    logger.info("Indexing file with id '%s'", file.id_)

    chain(
        group(
            extract_magic_file_type.signature(file_content, file),
            create_thumbnail.signature(file_content, file),
            tika_processing.signature(file_content, file),
            extract_loom_archive.signature(file_content),
        ),
        persist_processing_done.signature(file),
    ).delay().forget()
