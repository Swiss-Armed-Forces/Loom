from common.dependencies import get_celery_app

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


@persisting_task(app, IndexingPersister)
def persist_files_hidden_state(persister: IndexingPersister, hidden: bool):
    """Persists the file."""
    persister.set_hidden_state_file(hidden)
