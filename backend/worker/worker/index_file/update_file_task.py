import logging
from uuid import UUID

from celery import group
from common.dependencies import get_celery_app
from common.services.task_scheduling_service import UpdateFileRequest

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.sync_flag_to_imap import sync_flag_to_imap
from worker.index_file.tasks.update_file import update_file

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def update_task(file_id: UUID, request: UpdateFileRequest):
    logger.info("updating request: '%s' for id '%s'", request, file_id)
    tasks = [update_file.s(request, file_id)]
    if request.flagged is not None:
        tasks.append(sync_flag_to_imap.s(file_id, request.flagged))
    group(*tasks).delay().forget()
