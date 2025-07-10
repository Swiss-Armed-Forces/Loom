from typing import TypeVar
from uuid import UUID

from elasticsearch.dsl import Keyword

from common.models.es_repository import EsRepositoryObject, _EsRepositoryDocument


class RepositoryTaskObject(EsRepositoryObject):
    """An object which can be processed by the task pipeline."""

    state: str = "started"
    tasks_succeeded: list[UUID] = []
    tasks_retried: list[UUID] = []
    tasks_failed: list[UUID] = []


class _EsTaskDocument(_EsRepositoryDocument):
    state = Keyword()
    tasks_succeeded = Keyword(multi=True)
    tasks_retried = Keyword(multi=True)
    tasks_failed = Keyword(multi=True)


RepositoryTaskObjectT = TypeVar("RepositoryTaskObjectT", bound=RepositoryTaskObject)
SecondaryRepositoryTaskObjectT = TypeVar(
    "SecondaryRepositoryTaskObjectT", bound=RepositoryTaskObject
)
