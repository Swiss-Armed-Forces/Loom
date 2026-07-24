from datetime import datetime
from typing import Annotated, TypeVar
from uuid import UUID

from elasticsearch.dsl import Date, Float, InnerDoc, Keyword, Nested, Object
from pydantic import BaseModel, computed_field

from common.file.file_statistics import TermsStat
from common.models.es_repository import (
    EsRepositoryObject,
    ExcludeFromDefaultFields,
    _EsRepositoryDocument,
)


class TaskRun(BaseModel):
    started_at: datetime
    finished_at: datetime
    duration: float
    arguments: str | None = None
    exception: str | None = None


class TaskRecord(BaseModel):
    task_id: UUID
    task_name: str
    succeeded: list[TaskRun] = []
    retried: list[TaskRun] = []
    failed: list[TaskRun] = []


class RepositoryTaskObject(EsRepositoryObject):
    """An object which can be processed by the task pipeline."""

    state: str = "started"
    tasks: list[TaskRecord] = []

    @computed_field  # type: ignore[misc]
    @property
    def failed_task_names(
        self,
    ) -> Annotated[list[str], TermsStat(label="Failed Task Names")]:
        return list({t.task_name for t in self.tasks if t.failed})

    @computed_field  # type: ignore[misc]
    @property
    def retried_task_names(
        self,
    ) -> Annotated[list[str], TermsStat(label="Retried Task Names")]:
        return list({t.task_name for t in self.tasks if t.retried})

    @computed_field  # type: ignore[misc]
    @property
    def successful_task_names(
        self,
    ) -> Annotated[list[str], TermsStat(label="Successful Task Names")]:
        return list({t.task_name for t in self.tasks if t.succeeded})


class _EsTaskRun(InnerDoc):
    started_at = Date()
    finished_at = Date()
    duration = Float()
    arguments = Keyword()
    exception = Keyword()


class _EsTaskRecord(InnerDoc):
    task_id = Keyword()
    task_name = Keyword()
    succeeded = Object(_EsTaskRun, multi=True)
    retried = Object(_EsTaskRun, multi=True)
    failed = Object(_EsTaskRun, multi=True)


class _EsTaskDocument(_EsRepositoryDocument):
    state = Keyword()
    tasks = ExcludeFromDefaultFields(Nested(_EsTaskRecord, include_in_root=True))
    failed_task_names = Keyword(multi=True)
    retried_task_names = Keyword(multi=True)
    successful_task_names = Keyword(multi=True)


RepositoryTaskObjectT = TypeVar("RepositoryTaskObjectT", bound=RepositoryTaskObject)
SecondaryRepositoryTaskObjectT = TypeVar(
    "SecondaryRepositoryTaskObjectT", bound=RepositoryTaskObject
)
