import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import TYPE_CHECKING, Iterator, Union

from celery import Celery, Task
from redis import StrictRedis

from common.celery_app import get_terminal_queues
from common.services.queues_service import QueuesService
from common.settings import CELERY_QUEUE_NAME_MAXLEN, settings

if TYPE_CHECKING:
    from celery.app.control import _TaskInfo, _TaskScheduledInfo

    from common.celery_app import BaseTask

logger = logging.getLogger(__name__)

QUEUE_PAUSED_KEY_PREFIX = "queue_paused"


class TaskGroupName(str, Enum):
    PROCESSING = "processing"
    PERSISTING = "persisting"
    DISPATCH = "dispatch"


_task_groups: dict[str, list[str]] = {}


def register_task(group_name: TaskGroupName, task_name: str) -> None:
    """Register a task name into a named group."""
    _task_groups.setdefault(group_name.value, []).append(task_name)


def task_group(group_name: TaskGroupName) -> Callable[[Task], Task]:
    """Register a Celery task into a named group.

    Apply as the outermost decorator so the Celery task object (with .name) is
    received:

        @task_group(TaskGroupName.DISPATCH)
        @app.task()
        def my_task(...): ...
    """

    def decorator(task: Task) -> Task:
        _task_groups.setdefault(group_name.value, []).append(task.name)
        return task

    return decorator


_TASK_GROUP_KEY_PREFIX = "task_group"
_THROTTLED_KEY = "throttled"


class CeleryInspectService:
    def __init__(
        self,
        celery_app: "Celery[BaseTask]",
        queues_service: QueuesService,
        redis_client: StrictRedis,
    ):
        self._celery_app = celery_app
        self._queues_service = queues_service
        self._redis_client = redis_client

    def iterate_tasks(self) -> Iterator[Union["_TaskScheduledInfo", "_TaskInfo"]]:
        """Generator that yields individual celery tasks from all workers and states."""
        inspect = self._celery_app.control.inspect()
        inspect_methods = [inspect.active, inspect.scheduled, inspect.reserved]
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(method, safe=True) for method in inspect_methods]
            for future in futures:
                worker_tasks: (
                    dict[str, list["_TaskScheduledInfo"]]
                    | dict[str, list["_TaskInfo"]]
                    | None
                ) = future.result()
                if worker_tasks is None:
                    continue
                for _, tasks in worker_tasks.items():
                    yield from tasks

    def count_tasks(self) -> int:
        """Count total celery tasks across all workers and states."""
        return sum(1 for _ in self.iterate_tasks())

    def is_idle(
        self,
        called_from_task: bool = False,
        exclude_tasks: list[str] | None = None,
    ) -> bool:
        # Always exclude terminal queues — they have no consumers and can never be
        # drained by workers, so their message count must not block idle detection.
        excluded_queues = {
            self._task_name_to_queue(task_name) for task_name in exclude_tasks or []
        } | {q.name for q in get_terminal_queues()}
        all_counts = self._queues_service.get_all_queue_message_counts()
        tasks_count = self.count_tasks()
        messages_in_queues = sum(
            count for name, count in all_counts.items() if name not in excluded_queues
        )
        if called_from_task:
            # We are called from a celery task, so we need to subtract the task itself
            tasks_count -= 1
            # With task_acks_late=True the running task remains as an unacknowledged
            # message in its queue until it completes, so subtract that as well.
            messages_in_queues -= 1
        return messages_in_queues <= 0 and tasks_count <= 0

    def wait_for_idle(
        self,
        timeout: float,
        poll_interval: float = 10.0,
        called_from_task: bool = False,
        exclude_tasks: list[str] | None = None,
    ) -> bool:
        """Poll is_idle() until the system is idle or timeout is reached.

        Returns True if idle was reached within the timeout, False otherwise.
        """
        deadline = time.monotonic() + timeout
        while True:
            if self.is_idle(
                called_from_task=called_from_task,
                exclude_tasks=exclude_tasks,
            ):
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(poll_interval, remaining))

    def set_throttled(self, throttled: bool) -> None:
        """Set the system-wide throttle state and pause/resume the DISPATCH task
        group."""
        if throttled:
            self._redis_client.set(_THROTTLED_KEY, "1")
        else:
            self._redis_client.delete(_THROTTLED_KEY)
        self.set_taskgroup_paused(TaskGroupName.DISPATCH, throttled)

    def is_throttled(self) -> bool:
        """Return True if the system is currently throttled."""
        return bool(self._redis_client.exists(_THROTTLED_KEY))

    def get_throttled_tasks(self) -> list[str]:
        """Return the task names that are paused during throttling (the DISPATCH
        group)."""
        return self.get_task_names_in_group(TaskGroupName.DISPATCH.value)

    def _task_name_to_queue(self, task_name: str) -> str:
        return f"{settings.celery_queue_name_prefix}{task_name}"[
            :CELERY_QUEUE_NAME_MAXLEN
        ]

    def register_task_in_group(self, group_name: str, task_name: str) -> None:
        """Persist a task name into a group registry in Redis."""
        self._redis_client.sadd(f"{_TASK_GROUP_KEY_PREFIX}:{group_name}", task_name)

    def get_task_names_in_group(self, group_name: str) -> list[str]:
        """Return task names registered in the given group (reads from Redis)."""
        members = self._redis_client.smembers(f"{_TASK_GROUP_KEY_PREFIX}:{group_name}")
        return [m.decode() if isinstance(m, bytes) else m for m in members]

    def register_task_groups(self) -> None:
        """Persist all in-process task group registrations to Redis.

        Call on worker startup so the API process can look up group members.
        """
        for group_name, task_names in _task_groups.items():
            for task_name in task_names:
                self.register_task_in_group(group_name, task_name)

    def set_taskgroup_paused(
        self, task_group_name: TaskGroupName, paused: bool
    ) -> None:
        """Pause or resume all tasks in the given group."""
        for task_name in self.get_task_names_in_group(task_group_name.value):
            self.set_task_paused(task_name, paused)

    def is_taskgroup_paused(self, task_group_name: TaskGroupName) -> bool:
        """Return True if all tasks in the given group are paused."""
        task_names = self.get_task_names_in_group(task_group_name.value)
        return bool(task_names) and all(
            self.is_task_paused(name) for name in task_names
        )

    def set_task_paused(self, task_name: str, paused: bool) -> None:
        """Pause or resume processing for a single task by name."""
        queue = self._task_name_to_queue(task_name)
        self._queues_service.set_queue_paused(queue, paused)
        if paused:
            result = self._celery_app.control.cancel_consumer(queue, reply=True)
            logger.info(
                "Paused task %s (queue: %s), result=%s", task_name, queue, result
            )
        else:
            result = self._celery_app.control.add_consumer(queue, reply=True)
            logger.info(
                "Resumed task %s (queue: %s), result=%s", task_name, queue, result
            )

    def is_task_paused(self, task_name: str) -> bool:
        """Return True if the queue for the given task is currently paused."""
        return self._queues_service.is_queue_paused(self._task_name_to_queue(task_name))

    def restore_pause_state_on_worker(self, destination: list[str]) -> None:
        """Cancel consumers for any queue currently paused in Redis on a specific
        worker.

        Celery's cancel_consumer broadcast only reaches workers that are running at the
        time of the call. This must be called on worker startup so a newly started
        worker also stops consuming any queue that was paused before it came online.

        ``destination`` must target only the new worker so that already-running workers
        are not affected.
        """
        for queue in self._queues_service.get_paused_queues():
            logger.info(
                "Queue %s is paused; cancelling consumer on %s", queue, destination
            )
            self._celery_app.control.cancel_consumer(
                queue, destination=destination, reply=True
            )
