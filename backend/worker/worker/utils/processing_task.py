from abc import ABC, abstractmethod
from typing import Callable, Generic
from uuid import UUID

from celery.utils.log import get_task_logger
from common.celery_app import BaseTask
from common.dependencies import get_celery_app, get_root_task_information_repository
from common.models.base_repository import REPOSITORY_INSTANCES, BaseRepository
from common.task_object.task_object import (
    RepositoryTaskObjectT,
    SecondaryRepositoryTaskObjectT,
)
from common.utils.sharding import compute_shard, get_persister_shard_queue_name

from worker.settings import settings
from worker.utils.task_info_persister import TaskInfoPersister

logger = get_task_logger(__name__)
app = get_celery_app()


class ProcessingTask(
    BaseTask, ABC, Generic[RepositoryTaskObjectT, SecondaryRepositoryTaskObjectT]
):
    """A base task for all processing tasks.

    It keeps track of the status of task and subtask
    """

    # pylint does not consider metaclass:
    # https://stackoverflow.com/questions/22186843/pylint-w0223-method-is-abstract-in-class-but-is-not-overridden
    # pylint: disable=abstract-method

    @property
    @abstractmethod
    def _repository(
        self,
    ) -> (
        BaseRepository[RepositoryTaskObjectT]
        | BaseRepository[SecondaryRepositoryTaskObjectT]
    ):
        pass

    @staticmethod
    def _persist_fail(task_id: UUID, task_info_persister: TaskInfoPersister):
        task_info_persister.update_state("failed")
        task_info_persister.add_failed_task(task_id)

    @staticmethod
    def _persist_retry(task_id: UUID, task_info_persister: TaskInfoPersister):
        task_info_persister.add_retried_task(task_id)

    @staticmethod
    def _persist_success(task_id: UUID, task_info_persister: TaskInfoPersister):
        task_info_persister.add_success_task(task_id)

    def _get_object_id_for_request(self) -> UUID | None:
        """Look up object_id from RootTaskInformation for the current request."""
        try:
            root_task_id = UUID(self.request.root_id)
            repository = get_root_task_information_repository()
            root_task_information = repository.get_by_root_task_id(root_task_id)
            return root_task_information.object_id
        except (ValueError, AttributeError) as e:
            logger.error("Could not get object_id for task %s: %s", self.request.id, e)
            return None

    def _dispatch_persist_task(
        self,
        task_id: str,
        persist_callback: Callable[[UUID, TaskInfoPersister], None],
    ) -> None:
        """Dispatch a persist task to the appropriate shard queue."""
        object_id = self._get_object_id_for_request()
        if object_id is None:
            return
        shard = compute_shard(object_id, settings.num_persister_shards)
        queue = get_persister_shard_queue_name(shard)
        _persist_task_status_task.apply_async(
            args=(object_id, type(self._repository), UUID(task_id), persist_callback),
            queue=queue,
        ).forget()

    def on_failure(
        self, exc, task_id, args, kwargs, einfo
    ):  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self._dispatch_persist_task(task_id, ProcessingTask._persist_fail)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self, exc, task_id, args, kwargs, einfo
    ):  # pylint: disable=too-many-arguments, too-many-positional-arguments
        if settings.persist_retry_tasks:
            self._dispatch_persist_task(task_id, ProcessingTask._persist_retry)
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        if settings.persist_success_tasks:
            self._dispatch_persist_task(task_id, ProcessingTask._persist_success)
        return super().on_success(retval, task_id, args, kwargs)


@app.task()
def _persist_task_status_task(
    object_id: UUID,
    repository_type: type[BaseRepository],
    task_id: UUID,
    persist_callback: Callable[[UUID, TaskInfoPersister], None],
):
    class RepoBoundTaskInfoPersister(TaskInfoPersister[RepositoryTaskObjectT]):
        @classmethod
        def get_repository(cls) -> BaseRepository[RepositoryTaskObjectT]:
            repository = REPOSITORY_INSTANCES.get(repository_type)
            assert repository is not None
            return repository

    persister: TaskInfoPersister = RepoBoundTaskInfoPersister(object_id)
    persist_callback(task_id, persister)
