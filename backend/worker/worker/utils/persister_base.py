from abc import ABC, abstractmethod
from typing import Generic
from uuid import UUID

from common.models.base_repository import BaseRepository, RepositoryObjectT
from common.settings import settings
from common.utils.cache import cache_get, cache_set, invalidate
from elasticsearch import ConflictError


class PersistingException(Exception):
    """Exception raised when persisting a file fails."""


class PersisterBase(ABC, Generic[RepositoryObjectT]):
    """Base class for persisting values of a given file Has to be used in a `with
    PersisterBaseXY(file_id) as x:` statement to ensure that the file is saved."""

    @classmethod
    @abstractmethod
    def get_repository(cls) -> BaseRepository[RepositoryObjectT]:
        pass

    @classmethod
    def _cache_namespace(cls) -> str:
        """Cache namespace includes persister_id so each persister has its own cache."""
        return f"persister.{settings.persister_id}.{cls.__name__}"

    @classmethod
    def _cache_key(cls, object_id: UUID) -> tuple:
        """Cache key for a specific object."""
        return (str(object_id),)

    @classmethod
    def get_object_by_id(cls, object_id: UUID) -> RepositoryObjectT | None:
        # Check cache first
        cache_result = cache_get(cls._cache_namespace(), cls._cache_key, object_id)
        if cache_result.hit:
            cached_obj = cache_result.value
            if cached_obj is None:
                return None
            # Validate cache freshness using repository method
            if cls.get_repository().is_fresh(cached_obj):
                # Cache is fresh - return cached object
                return cached_obj
            # Cache is stale - invalidate it
            invalidate(cls._cache_namespace(), cls._cache_key, object_id)

        # Cache miss - fetch from repository
        obj = cls.get_repository().get_by_id(object_id)
        if obj is not None:
            cache_set(cls._cache_namespace(), cls._cache_key, obj, object_id)
        return obj

    def __init__(self, object_id: UUID):
        self._object_id = object_id
        self._object: RepositoryObjectT
        self._snapshot: RepositoryObjectT

    def __enter__(self):
        object_ = self.get_object_by_id(self._object_id)
        if object_ is None:
            raise PersistingException(
                f"Could not get object with id '{self._object_id}' from repository"
            )
        self._object = object_
        self._snapshot = self._object.model_copy(deep=True)
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type:
            return

        dirty_fields = self._compute_dirty_fields()

        if not dirty_fields:
            return  # Nothing changed, skip persist entirely

        try:
            self.get_repository().update(self._object, include=dirty_fields)
        except ConflictError as ex:
            # Another process updated the document - invalidate cache and raise
            invalidate(self._cache_namespace(), self._cache_key, self._object_id)
            raise PersistingException(
                f"Concurrent modification detected for object '{self._object_id}'",
            ) from ex

        # Update cache with modified object
        cache_set(
            self._cache_namespace(),
            self._cache_key,
            self._object,
            self._object_id,
        )

    def _compute_dirty_fields(self) -> set[str]:
        """Compare current state with snapshot to find changed fields.

        Checks both regular fields (model_fields) and computed fields
        (model_computed_fields) to ensure derived values are also updated.
        """
        dirty: set[str] = set()

        # Check regular fields
        for field_name in self._object.model_fields:
            current_value = getattr(self._object, field_name)
            snapshot_value = getattr(self._snapshot, field_name)
            if current_value != snapshot_value:
                dirty.add(field_name)

        # Check computed fields (e.g., full_path, short_name, extension)
        for field_name in self._object.model_computed_fields:
            current_value = getattr(self._object, field_name)
            snapshot_value = getattr(self._snapshot, field_name)
            if current_value != snapshot_value:
                dirty.add(field_name)

        return dirty
