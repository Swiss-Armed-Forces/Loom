from typing import TypeVar
from uuid import UUID

from elasticsearch_dsl import Keyword
from pydantic import computed_field

from common.models.es_repository import EsRepositoryObject, _EsRepositoryDocument


class RepositoryTaskObject(EsRepositoryObject):
    """An object which can be processed by the task pipeline."""

    @computed_field  # type: ignore[misc]
    @property
    def root_task_id(self) -> UUID:
        return self.id_

    state: str = "started"
    tasks_succeeded: list[UUID] = []
    tasks_retried: list[UUID] = []
    tasks_failed: list[UUID] = []


class _EsTaskDocument(_EsRepositoryDocument):
    root_task_id = Keyword()
    state = Keyword()
    tasks_succeeded = Keyword(multi=True)
    tasks_retried = Keyword(multi=True)
    tasks_failed = Keyword(multi=True)


RepositoryTaskObjectT = TypeVar("RepositoryTaskObjectT", bound=RepositoryTaskObject)
SecondaryRepositoryTaskObjectT = TypeVar(
    "SecondaryRepositoryTaskObjectT", bound=RepositoryTaskObject
)
