from typing import Any

from celery import chain
from celery.canvas import Signature
from common.archive.archive_repository import Archive
from common.dependencies import get_celery_app

from worker.create_archive.infra.archive_creation_persister import (
    ArchiveCreationPersister,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.utils.async_task_branch import (
    WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    AsyncBranchesNotCompleted,
    raise_if_has_incomplete_async_branches,
)
from worker.utils.persisting_task import persisting_task

app = get_celery_app()


def signature(archive: Archive) -> Signature:
    """Create the signature for the task that persists the processing done status."""
    return chain(
        wait_for_async_branches_to_complete.s(),
        persist_processing_done_task.s(archive),
    )


@app.task(
    bind=True,
    base=ArchiveProcessingTask,
    autoretry_for=tuple([AsyncBranchesNotCompleted]),
    retry_backoff=True,
    max_retries=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
)
def wait_for_async_branches_to_complete(self: ArchiveProcessingTask, args: Any):
    raise_if_has_incomplete_async_branches(self)
    return args


@persisting_task(app, ArchiveCreationPersister)
def persist_processing_done_task(persister: ArchiveCreationPersister, _: Any):
    """Task that persists the processing done status."""
    persister.set_state("created")
