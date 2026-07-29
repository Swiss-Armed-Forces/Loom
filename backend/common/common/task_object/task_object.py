from datetime import datetime
from typing import Annotated, TypeVar
from uuid import UUID

from elasticsearch.dsl import Date, Float, InnerDoc, Integer, Keyword, Nested, Object
from pydantic import BaseModel, computed_field

from common.file.file_statistics import TermsStat
from common.models.es_repository import (
    EsRepositoryObject,
    ExcludeFromDefaultFields,
    _EsRepositoryDocument,
)


class TaskRun(BaseModel):
    task_id: UUID
    started_at: datetime
    finished_at: datetime
    duration: float
    arguments: str | None = None
    exception: str | None = None


class TaskRecord(BaseModel):
    task_name: str
    avg_duration: float = 0
    run_count: int = 0
    succeeded: list[TaskRun] | None = None
    retried: list[TaskRun] | None = None
    failed: list[TaskRun] | None = None


class RepositoryTaskObject(EsRepositoryObject):
    """An object which can be processed by the task pipeline."""

    state: str = "started"
    tasks: list[TaskRecord] = []

    @computed_field  # type: ignore[misc]
    @property
    def failed_task_names(
        self,
    ) -> Annotated[list[str] | None, TermsStat(label="Failed Task Names")]:
        names = list({t.task_name for t in self.tasks if t.failed})
        return names if len(names) > 0 else None

    @computed_field  # type: ignore[misc]
    @property
    def retried_task_names(
        self,
    ) -> Annotated[list[str] | None, TermsStat(label="Retried Task Names")]:
        names = list({t.task_name for t in self.tasks if t.retried})
        return names if len(names) > 0 else None

    @computed_field  # type: ignore[misc]
    @property
    def successful_task_names(
        self,
    ) -> Annotated[list[str] | None, TermsStat(label="Successful Task Names")]:
        names = list({t.task_name for t in self.tasks if t.succeeded})
        return names if len(names) > 0 else None


class _EsTaskRun(InnerDoc):
    task_id = Keyword()
    started_at = Date()
    finished_at = Date()
    duration = Float()
    arguments = Keyword()
    exception = Keyword()


class _EsTaskRecord(InnerDoc):
    task_name = Keyword()
    succeeded = Object(_EsTaskRun, multi=True)
    retried = Object(_EsTaskRun, multi=True)
    avg_duration = Float()
    run_count = Integer()
    failed = Object(_EsTaskRun, multi=True)


class _EsTaskDocument(_EsRepositoryDocument):
    state = Keyword()
    tasks = ExcludeFromDefaultFields(Nested(_EsTaskRecord, include_in_root=True))
    failed_task_names = ExcludeFromDefaultFields(Keyword(multi=True))
    retried_task_names = ExcludeFromDefaultFields(Keyword(multi=True))
    successful_task_names = ExcludeFromDefaultFields(Keyword(multi=True))


RepositoryTaskObjectT = TypeVar("RepositoryTaskObjectT", bound=RepositoryTaskObject)
SecondaryRepositoryTaskObjectT = TypeVar(
    "SecondaryRepositoryTaskObjectT", bound=RepositoryTaskObject
)
