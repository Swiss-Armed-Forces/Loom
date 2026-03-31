from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

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


class BaseRepository(ABC, Generic[RepositoryObjectT]):
    """Repository for CRUD operations."""

    def __init__(self):
        REPOSITORY_INSTANCES[type(self)] = self

    @property
    @abstractmethod
    def _object_type(self) -> type[RepositoryObjectT]:
        pass

    @abstractmethod
    def is_fresh(self, obj: RepositoryObjectT) -> bool:
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


REPOSITORY_INSTANCES: dict[type[BaseRepository], BaseRepository] = {}
