from typing import Generic
from uuid import UUID

from common.task_object.task_object import (
    RepositoryTaskObject,
    RepositoryTaskObjectT,
    TaskRecord,
    TaskRun,
)

from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _update_state(obj: RepositoryTaskObject, state: str) -> None:
    obj.state = state


def _add_failed_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_id: UUID, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_id, task_name)
    record.failed.append(task_run)


def _add_retried_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_id: UUID, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_id, task_name)
    record.retried.append(task_run)


def _add_success_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_id: UUID, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_id, task_name)
    record.succeeded.append(task_run)


def _get_or_create_task_record(
    obj: RepositoryTaskObject, task_id: UUID, task_name: str
) -> TaskRecord:
    if isinstance(task_id, str):
        task_id = UUID(task_id)

    task_record = next(
        (record for record in obj.tasks if record.task_id == task_id),
        None,
    )
    if not task_record:
        task_record = TaskRecord(
            task_id=task_id,
            task_name=task_name,
            succeeded=[],
            retried=[],
            failed=[],
        )
        obj.tasks.append(task_record)
    return task_record


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
