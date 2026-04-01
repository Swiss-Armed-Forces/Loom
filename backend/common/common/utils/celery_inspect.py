import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Iterator, Union

from common.dependencies import get_celery_app, get_queues_service

if TYPE_CHECKING:
    from celery.app.control import _TaskInfo, _TaskScheduledInfo


logger = logging.getLogger(__name__)


def get_messages_in_queues() -> int:
    queues = get_queues_service()
    return queues.get_message_count()


def iterate_celery_tasks() -> Iterator[Union["_TaskScheduledInfo", "_TaskInfo"]]:
    """Generator that yields individual celery tasks from all workers and states."""
    inspect = get_celery_app().control.inspect()

    inspect_methods = [inspect.active, inspect.scheduled, inspect.reserved]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(method, safe=True) for method in inspect_methods]

        for future in futures:
            worker_tasks: (
                dict[str, list[_TaskScheduledInfo]] | dict[str, list[_TaskInfo]] | None
            ) = future.result()
            if worker_tasks is None:
                continue

            # Iterate through each worker's tasks
            for _, tasks in worker_tasks.items():
                yield from tasks


def get_celery_tasks_count() -> int:
    """Count total celery tasks using the iterator."""
    return sum(1 for _ in iterate_celery_tasks())


def is_celery_idle(called_from_task=False) -> bool:
    celery_tasks_count = get_celery_tasks_count()
    messages_in_queues = get_messages_in_queues()
    if called_from_task:
        # We are called from a celery task, so we need to subtract the task itself
        celery_tasks_count -= 1
    return messages_in_queues <= 0 and celery_tasks_count <= 0
