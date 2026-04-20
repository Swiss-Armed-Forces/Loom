from common.dependencies import get_celery_app
from common.services.task_scheduling_service import UpdateArchiveRequest

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, ArchiveCreationPersister)
def update_archive(persister: ArchiveCreationPersister, request: UpdateArchiveRequest):
    if request.hidden is not None:
        persister.set_hidden(request.hidden)
