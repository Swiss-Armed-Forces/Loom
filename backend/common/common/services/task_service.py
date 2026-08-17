"""Base task service providing shared Celery dispatch infrastructure."""

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
