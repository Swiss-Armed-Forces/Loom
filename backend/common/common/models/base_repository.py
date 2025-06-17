from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


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
    def save(self, obj: RepositoryObjectT):
        pass

    @abstractmethod
    def get_by_id(self, id_: Any) -> RepositoryObjectT | None:
        pass


REPOSITORY_INSTANCES: dict[type[BaseRepository], BaseRepository] = {}
