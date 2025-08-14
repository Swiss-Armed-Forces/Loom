from typing import Any
from uuid import UUID, uuid4

from celery import Task
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_root_task_information_repository

app = get_celery_app()

# We should check this regularly, therefore we set this to quite a high number.
WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES = 200
WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX = 30


class AsyncBranchesNotCompleted(Exception):
    """Raised when there are incomplet async branches detected."""


def complete_async_branch(task: Task) -> Signature:
    async_branch_id = uuid4()
    root_task_id = UUID(task.request.root_id)

    # Register started branch
    repository = get_root_task_information_repository()
    repository.add_started_async_branch(root_task_id, async_branch_id)
    return _complete_async_branch_task.s(root_task_id, async_branch_id)


def raise_if_has_incomplete_async_branches(task: Task):
    root_task_id = UUID(task.request.root_id)
    repository = get_root_task_information_repository()
    root_task_information = repository.get_by_root_task_id(root_task_id)
    if set(root_task_information.started_async_branches) != set(
        root_task_information.completed_async_branches
    ):
        raise AsyncBranchesNotCompleted


# Note: we specifically don't set a base here, especially not for a ProcessingTask.
# this is to avoid overloading the repository with lots of "retried task"-updates.
@app.task(
    bind=True,
    autoretry_for=tuple([AsyncBranchesNotCompleted]),
    retry_backoff=True,
    max_retries=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES,
    retry_backoff_max=WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_RETRY_BACKOFF_MAX,
)
def wait_for_async_branches_to_complete(self: Task, args: Any):
    raise_if_has_incomplete_async_branches(self)
    return args


@app.task()
def _complete_async_branch_task(_: Any, root_task_id: UUID, async_branch_id: UUID):
    repository = get_root_task_information_repository()
    repository.add_completed_async_branch(root_task_id, async_branch_id)
