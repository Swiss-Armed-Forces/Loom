from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Iterator, Sequence, TypeVar

import typing_extensions
from pydantic import BaseModel, ConfigDict

# Type alias for Pydantic's include/exclude format
IncEx: typing_extensions.TypeAlias = (
    set[int] | set[str] | dict[int, Any] | dict[str, Any] | None
)


class RepositoryObject(BaseModel, ABC):
    """An object that can be stored in the repository."""

    model_config = ConfigDict(validate_assignment=True)

    @property
    @abstractmethod
    def id_(self) -> Any:
        raise NotImplementedError("id_ field not implemented")


RepositoryObjectT = TypeVar("RepositoryObjectT", bound=RepositoryObject)


class RepositoryBulkSaveError(Exception):
    """Raised when a bulk_save operation fails."""


@dataclass
class BulkOperationResult:
    """Result for a single object in a bulk operation."""

    object_id: Any
    success: bool
    error: RepositoryBulkSaveError | None = None


class BaseRepository(ABC, Generic[RepositoryObjectT]):
    """Repository for CRUD operations."""

    def __init__(self):
        REPOSITORY_INSTANCES[type(self)] = self

    @property
    @abstractmethod
    def _object_type(self) -> type[RepositoryObjectT]:
        pass

    @abstractmethod
    def save(self, obj: RepositoryObjectT):
        pass

    @abstractmethod
    def get_by_id(self, id_: Any) -> RepositoryObjectT | None:
        pass

    @abstractmethod
    def update(
        self,
        obj: RepositoryObjectT,
        include: IncEx = None,
        exclude: IncEx = None,
    ):
        """Partial update of specific fields."""

    def bulk_save(
        self, objects: Sequence[RepositoryObjectT]
    ) -> Iterator[BulkOperationResult]:
        """Persist multiple objects.

        Yields results as they complete.
        """
        for obj in objects:
            try:
                self.save(obj)
                yield BulkOperationResult(object_id=obj.id_, success=True)
            except Exception as ex:  # pylint: disable=broad-exception-caught
                yield BulkOperationResult(
                    object_id=obj.id_,
                    success=False,
                    error=RepositoryBulkSaveError(f"{ex}"),
                )


REPOSITORY_INSTANCES: dict[type[BaseRepository], BaseRepository] = {}
