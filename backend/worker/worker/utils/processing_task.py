from abc import ABC, abstractmethod
from typing import Callable, Generic
from uuid import UUID

from celery import Task
from celery.utils.log import get_task_logger
from common.dependencies import get_celery_app, get_root_task_information_repository
from common.models.base_repository import REPOSITORY_INSTANCES, BaseRepository
from common.task_object.task_object import (
    RepositoryTaskObjectT,
    SecondaryRepositoryTaskObjectT,
)

from worker.settings import settings
from worker.utils.persister_base import PersistingException
from worker.utils.task_info_persister import TaskInfoPersister

PERSIST_MAX_RETRIES = 15

logger = get_task_logger(__name__)
app = get_celery_app()


class ProcessingTask(
    ABC, Task, Generic[RepositoryTaskObjectT, SecondaryRepositoryTaskObjectT]
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

    def on_failure(
        self, exc, task_id, args, kwargs, einfo
    ):  # pylint: disable=too-many-arguments
        _persist_task_status_task.delay(
            type(self._repository), task_id, ProcessingTask._persist_fail
        ).forget()
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self, exc, task_id, args, kwargs, einfo
    ):  # pylint: disable=too-many-arguments
        if settings.persist_retry_tasks:
            _persist_task_status_task.delay(
                type(self._repository), task_id, ProcessingTask._persist_retry
            ).forget()
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        if settings.persist_success_tasks:
            _persist_task_status_task.delay(
                type(self._repository), task_id, ProcessingTask._persist_success
            ).forget()
        return super().on_success(retval, task_id, args, kwargs)


@app.task(
    bind=True,
    autoretry_for=tuple([PersistingException]),
    max_retries=PERSIST_MAX_RETRIES,
    retry_backoff=True,
)
def _persist_task_status_task(
    task: Task,
    repository_type: type[BaseRepository],
    task_id: UUID,
    persist_callback: Callable[[UUID, TaskInfoPersister], None],
):
    object_id = _get_object_id_from_task(task)

    class RepoBoundTaskInfoPersister(TaskInfoPersister[RepositoryTaskObjectT]):
        @classmethod
        def get_repository(cls) -> BaseRepository[RepositoryTaskObjectT]:
            repository = REPOSITORY_INSTANCES.get(repository_type)
            assert repository is not None
            return repository

    with RepoBoundTaskInfoPersister(object_id) as persister:
        persist_callback(task_id, persister)


def _get_object_id_from_task(task: Task) -> UUID:
    root_task_id = UUID(task.request.root_id)
    repository = get_root_task_information_repository()
    root_task_information = repository.get_by_root_task_id(root_task_id)
    return root_task_information.object_id
