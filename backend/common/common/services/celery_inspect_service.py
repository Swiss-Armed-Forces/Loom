import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Iterator, Union

from celery import Celery
from redis import StrictRedis

from common.celery_app import get_terminal_queues
from common.services.queues_service import QueuesService

if TYPE_CHECKING:
    from celery.app.control import _TaskInfo, _TaskScheduledInfo

    from common.celery_app import BaseTask

logger = logging.getLogger(__name__)

QUEUE_PAUSED_KEY_PREFIX = "queue_paused"


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

    def count_messages_in_queues(self, exclude_queues: list[str] | None = None) -> int:
        all_counts = self._queues_service.get_all_queue_message_counts()
        exclude = set(exclude_queues or [])
        return sum(count for name, count in all_counts.items() if name not in exclude)

    def is_idle(
        self, called_from_task: bool = False, exclude_queues: list[str] | None = None
    ) -> bool:
        # Always exclude terminal queues — they have no consumers and can never be
        # drained by workers, so their message count must not block idle detection.
        effective_excludes = list(
            {q.name for q in get_terminal_queues()} | set(exclude_queues or [])
        )
        tasks_count = self.count_tasks()
        messages_in_queues = self.count_messages_in_queues(
            exclude_queues=effective_excludes
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
        exclude_queues: list[str] | None = None,
    ) -> bool:
        """Poll is_idle() until the system is idle or timeout is reached.

        Returns True if idle was reached within the timeout, False otherwise.
        """
        deadline = time.monotonic() + timeout
        while True:
            if self.is_idle(
                called_from_task=called_from_task, exclude_queues=exclude_queues
            ):
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(poll_interval, remaining))

    def set_queue_paused(self, queue_name: str, paused: bool) -> None:
        """Persist queue pause state in Redis and broadcast to all current workers."""
        key = f"{QUEUE_PAUSED_KEY_PREFIX}:{queue_name}"
        if paused:
            self._redis_client.set(key, "1")
        else:
            self._redis_client.delete(key)
        if paused:
            result = self._celery_app.control.cancel_consumer(queue_name, reply=True)
        else:
            result = self._celery_app.control.add_consumer(queue_name, reply=True)
        logger.info(
            "%s queue %s, result=%s",
            "Paused" if paused else "Resumed",
            queue_name,
            result,
        )

    def is_queue_paused(self, queue_name: str) -> bool:
        """Check if a queue is currently paused according to Redis state."""
        return bool(
            self._redis_client.exists(f"{QUEUE_PAUSED_KEY_PREFIX}:{queue_name}")
        )

    def get_paused_queues(self) -> list[str]:
        """Return all queue names that are currently paused in Redis."""
        prefix = f"{QUEUE_PAUSED_KEY_PREFIX}:"
        return [
            key.decode().removeprefix(prefix)
            for key in self._redis_client.keys(f"{prefix}*")
        ]
