from typing import Generic
from uuid import UUID

from common.task_object.task_object import RepositoryTaskObjectT

from worker.utils.persister_base import PersisterBase


class TaskInfoPersister(
    Generic[RepositoryTaskObjectT], PersisterBase[RepositoryTaskObjectT]
):
    """Persist information about the task, e.g. which tasks have failed, which tasks
    have succeeded, etc.

    Has to be used in a `with TaskInfoPersister(file_id) as x:` statement to ensure that
    the file is saved
    """

    def update_state(self, state: str):
        self._object.state = state

    def add_failed_task(self, task_id: UUID):
        self._object.tasks_failed.append(task_id)

    def add_retried_task(self, task_id: UUID):
        self._object.tasks_retried.append(task_id)

    def add_success_task(self, task_id: UUID):
        self._object.tasks_succeeded.append(task_id)
