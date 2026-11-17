"""Base task service providing shared Celery dispatch infrastructure."""

from enum import IntEnum
from typing import Optional
from uuid import UUID

from celery import Celery
from celery.result import AsyncResult

from common.celery_app import BaseTask
from common.settings import settings
from common.task_object.root_task_information_repository import (
    RootTaskInformationRepository,
)
from common.utils.sharding import compute_shard, get_persister_shard_name


class TaskPriority(IntEnum):
    """Priority carried by a task message, higher favoured by the broker.

    Quorum queues are the only kind loom declares, and on the RabbitMQ 4.1 the chart
    pins they carry two bands rather than graded levels: [0, 4] is normal and anything
    above 4 is high, with high favoured over normal at a 2:1 ratio. Only the step from
    MEDIUM to HIGH therefore changes where a message lands -- LOW and MEDIUM share the
    normal band, and HIGH is the first value in the other one. `x-max-priority` is what
    opts a *classic* queue into priorities and is ignored by quorum queues, so the
    priority on the message is all that is needed.
    """

    LOW = 0
    MEDIUM = 4
    HIGH = 5


class TaskService:
    """Base class providing common task dispatch infrastructure."""

    def __init__(
        self,
        celery_app: "Celery[BaseTask]",
        root_task_information_repository: RootTaskInformationRepository,
    ) -> None:
        self._celery_app = celery_app
        self._root_task_information_repository = root_task_information_repository

    @property
    def celery_app(self) -> "Celery[BaseTask]":
        return self._celery_app

    def _send_task(
        self,
        task_name: str,
        args: list,
        root_id: str,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> AsyncResult:
        """Send a task to its dedicated queue via the shared exchange routing key.

        Always sets routing_key=task_name so the shared exchange routes the message to
        the correct dedicated queue, regardless of whether task_routes has been
        populated in the sending process (e.g. the API process never calls
        register_tasks_for_package, so task_routes is empty there).

        Returns the AsyncResult so the caller can decide whether to .forget() it or
        track it.
        """
        kwargs: dict = {}
        if task_id is not None:
            kwargs["task_id"] = task_id
        return self._celery_app.send_task(
            task_name,
            args=args,
            root_id=root_id,
            routing_key=task_name,
            priority=priority,
            **kwargs,
        )

    def _send_persisting_task(
        self,
        task_name: str,
        args: list,
        root_id: str,
        entity_id: UUID,
    ) -> AsyncResult:
        """Send a task routed to the persister shard for the given entity."""
        shard = compute_shard(entity_id, settings.num_persister_shards)
        return self._celery_app.send_task(
            task_name,
            args=args,
            root_id=root_id,
            routing_key=get_persister_shard_name(shard),
        )
