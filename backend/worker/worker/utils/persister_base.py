from abc import ABC, abstractmethod
from typing import Generic
from uuid import UUID

from common.models.base_repository import BaseRepository, RepositoryObjectT


class PersistingException(Exception):
    """Exception raised when persisting a file fails."""


class PersisterBase(ABC, Generic[RepositoryObjectT]):
    """Base class for persisting values of a given file Has to be used in a `with
    PersisterBaseXY(file_id) as x:` statement to ensure that the file is saved."""

    @classmethod
    @abstractmethod
    def get_repository(cls) -> BaseRepository[RepositoryObjectT]:
        pass

    def __init__(self, object_id: UUID):
        self._object_id = object_id
        self._object: RepositoryObjectT

    def __enter__(self):
        self._object = self.get_repository().get_by_id(self._object_id)
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type:
            return
        try:
            self.get_repository().save(self._object)
        except Exception as ex:
            raise PersistingException() from ex
