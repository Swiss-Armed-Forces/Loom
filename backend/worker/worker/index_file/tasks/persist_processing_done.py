from typing import Any

from celery import chain
from celery.canvas import Signature
from common.dependencies import get_celery_app
from common.file.file_repository import File

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.async_task_branch import wait_for_async_branches_to_complete
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(file: File) -> Signature:
    """Create the signature for the task that persists the processing done status."""
    return chain(
        wait_for_async_branches_to_complete.s(),
        persist_processing_done_task.s(file),
    )


@persisting_task(app, IndexingPersister)
def persist_processing_done_task(persister: IndexingPersister, _: Any):
    """Task that persists the processing done status."""
    persister.set_state("processed")
