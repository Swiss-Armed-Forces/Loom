from typing import Generic

from common.task_object.task_object import (
    RepositoryTaskObject,
    RepositoryTaskObjectT,
    TaskRecord,
    TaskRun,
)

from worker.settings import settings
from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _update_state(obj: RepositoryTaskObject, state: str) -> None:
    obj.state = state


def _add_failed_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_name)
    if not record.failed:
        record.failed = []
    elif len(record.failed) >= settings.max_no_of_persisted_failed_tasks:
        _remove_oldest_task_run(record.failed)
    record.failed.append(task_run)
    _increase_count_and_recalculate_avg_duration(record, task_run.duration)


def _add_retried_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_name)
    if not record.retried:
        record.retried = []
    elif len(record.retried) >= settings.max_no_of_persisted_retried_tasks:
        _remove_oldest_task_run(record.retried)
    record.retried.append(task_run)
    _increase_count_and_recalculate_avg_duration(record, task_run.duration)


def _add_success_task(
    obj: RepositoryTaskObject, task_run: TaskRun, task_name: str
) -> None:
    record = _get_or_create_task_record(obj, task_name)
    if not record.succeeded:
        record.succeeded = []
    elif len(record.succeeded) >= settings.max_no_of_persisted_succeeded_tasks:
        _remove_oldest_task_run(record.succeeded)
    record.succeeded.append(task_run)
    _increase_count_and_recalculate_avg_duration(record, task_run.duration)


def _remove_oldest_task_run(runs: list[TaskRun]):
    oldest_idx = min(range(len(runs)), key=lambda i: runs[i].started_at)
    del runs[oldest_idx]


def _increase_count_and_recalculate_avg_duration(
    task_record: TaskRecord, duration: float
):
    n = task_record.run_count + 1
    task_record.avg_duration = (
        task_record.avg_duration * task_record.run_count / n + duration / n
    )
    task_record.run_count = n


def _get_or_create_task_record(obj: RepositoryTaskObject, task_name: str) -> TaskRecord:
    task_record = next(
        (record for record in obj.tasks if record.task_name == task_name),
        None,
    )
    if not task_record:
        task_record = TaskRecord(task_name=task_name)
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
