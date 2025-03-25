from typing import Any
from uuid import UUID, uuid4

from celery import Task
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_root_task_information_repository

app = get_celery_app()


WAIT_FOR_ASYNC_BRANCHES_TO_COMPLETE_MAX_RETRIES = 15


class AsyncBranchesNotCompleted(Exception):
    """Raised when there are incomplet async branches detected."""


def complete_async_branch(task: Task) -> Signature:
    async_branch_id = uuid4()
    root_task_id = UUID(task.request.root_id)

    repository = get_root_task_information_repository()
    root_task_information = repository.get_by_root_task_id(root_task_id)
    root_task_information.started_async_branches.append(async_branch_id)
    repository.save(root_task_information)
    return _complete_async_branch_task.s(root_task_id, async_branch_id)


def raise_if_has_incomplete_async_branches(task: Task):
    root_task_id = UUID(task.request.root_id)
    repository = get_root_task_information_repository()
    root_task_information = repository.get_by_root_task_id(root_task_id)
    if set(root_task_information.started_async_branches) != set(
        root_task_information.completed_async_branches
    ):
        raise AsyncBranchesNotCompleted


@app.task()
def _complete_async_branch_task(_: Any, root_task_id: UUID, async_branch_id: UUID):
    repository = get_root_task_information_repository()
    root_task_information = repository.get_by_root_task_id(root_task_id)
    root_task_information.completed_async_branches.append(async_branch_id)
    repository.save(root_task_information)
