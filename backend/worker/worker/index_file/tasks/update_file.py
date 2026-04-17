from common.dependencies import get_celery_app
from common.services.task_scheduling_service import UpdateFileRequest

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, IndexingPersister)
def update_file(persister: IndexingPersister, request: UpdateFileRequest):
    if request.hidden is not None:
        persister.set_hidden(request.hidden)

    if request.flagged is not None:
        persister.set_flagged(request.flagged)

    if request.seen is not None:
        persister.set_seen(request.seen)
