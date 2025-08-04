from typing import Any

from celery import chain
from celery.canvas import Signature
from common.dependencies import get_celery_app
from common.file.file_repository import File

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.async_task_branch import (
    WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX,
    AsyncBranchesNotCompleted,
    raise_if_has_incomplete_async_branches,
)
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(file: File) -> Signature:
    """Create the signature for the task that persists the processing done status."""
    return chain(
        wait_for_async_branches_to_complete.s(),
        persist_processing_done_task.s(file),
    )


@app.task(
    bind=True,
    base=FileIndexingTask,
    autoretry_for=tuple([AsyncBranchesNotCompleted]),
    retry_backoff=True,
    max_retries=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    retry_backoff_max=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX,
)
def wait_for_async_branches_to_complete(self: FileIndexingTask, args: Any):
    raise_if_has_incomplete_async_branches(self)
    return args


@persisting_task(app, IndexingPersister)
def persist_processing_done_task(persister: IndexingPersister, _: Any):
    """Task that persists the processing done status."""
    persister.set_state("processed")
