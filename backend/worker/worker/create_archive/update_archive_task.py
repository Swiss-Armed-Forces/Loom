import logging
from uuid import UUID

from celery import chain
from common.dependencies import get_celery_app
from common.services.task_scheduling_service import UpdateArchiveRequest

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks import persist_processing_done
from worker.create_archive.tasks.update_archive import update_archive

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def update_task(archive_id: UUID, request: UpdateArchiveRequest):
    logger.info("updating request: '%s' for id '%s'", request, archive_id)
    chain(
        update_archive.s(request, archive_id),
        persist_processing_done.signature(archive_id),
    ).delay().forget()
