from typing import Generic
from uuid import UUID

from common.task_object.task_object import RepositoryTaskObject, RepositoryTaskObjectT

from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _update_state(obj: RepositoryTaskObject, state: str) -> None:
    obj.state = state


def _add_failed_task(obj: RepositoryTaskObject, task_id: UUID) -> None:
    obj.tasks_failed.append(task_id)


def _add_retried_task(obj: RepositoryTaskObject, task_id: UUID) -> None:
    obj.tasks_retried.append(task_id)


def _add_success_task(obj: RepositoryTaskObject, task_id: UUID) -> None:
    obj.tasks_succeeded.append(task_id)


class TaskInfoPersister(
    Generic[RepositoryTaskObjectT], PersisterBase[RepositoryTaskObjectT]
):
    """Persist information about the task, e.g. which tasks have failed, which tasks
    have succeeded, etc."""

    # Bind mutations as class attributes
    update_state = mutation(_update_state)
    add_failed_task = mutation(_add_failed_task)
    add_retried_task = mutation(_add_retried_task)
    add_success_task = mutation(_add_success_task)
