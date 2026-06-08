import logging

from celery import chain, group
from common.dependencies import get_celery_app
from common.file.file_repository import File
from common.services.lazybytes_service import TempLazyBytes

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
def index_file_task(file: File, file_content: TempLazyBytes):
    logger.info("Indexing file with id '%s'", file.id_)

    chain(
        group(
            create_thumbnail.signature(file, file_content),
            render.signature(file, file_content),
            tika_processing.signature(file_content, file),
        ),
        persist_processing_done.signature(file.id_),
    ).delay().forget()
