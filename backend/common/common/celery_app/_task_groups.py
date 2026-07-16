from collections.abc import Callable
from enum import Enum

from celery import Task


class TaskGroupName(str, Enum):
    ALL = "all"
    PROCESSING = "processing"
    PERSISTING = "persisting"
    PERIODIC = "periodic"
    DISPATCH = "dispatch"


_task_groups: dict[TaskGroupName, list[str]] = {}


def register_task(group_name: TaskGroupName, task_name: str) -> None:
    """Register a task name into a named group."""
    _task_groups.setdefault(group_name, []).append(task_name)


def task_group(group_name: TaskGroupName) -> Callable[[Task], Task]:
    """Register a Celery task into a named group.

    Apply as the outermost decorator so the Celery task object (with .name) is
    received:

        @task_group(TaskGroupName.DISPATCH)
        @app.task()
        def my_task(...): ...
    """

    def decorator(task: Task) -> Task:
        _task_groups.setdefault(group_name, []).append(task.name)
        return task

    return decorator
