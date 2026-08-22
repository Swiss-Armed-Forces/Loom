import logging
from uuid import UUID

from common.dependencies import get_archive_repository, get_celery_app

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def delete_archive_task(archive_id: UUID):
    logger.info("deleting archive '%s'", archive_id)
    get_archive_repository().delete_by_id(archive_id)
