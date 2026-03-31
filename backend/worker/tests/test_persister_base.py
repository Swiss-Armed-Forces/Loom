# pylint: disable=protected-access
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from common.dependencies import get_redis_cache_client
from common.models.base_repository import BaseRepository, RepositoryObject
from elasticsearch import ConflictError
from pydantic import computed_field

from worker.utils.persister_base import PersisterBase, PersistingException


@pytest.fixture(autouse=True)
def configure_cache_mock():
    """Configure the mock Redis cache client for cache miss behavior."""
    redis_cache = get_redis_cache_client()
    redis_cache.hget.return_value = None  # Simulate cache miss
    redis_cache.hdel.return_value = 1  # Simulate successful deletion


class MockRepositoryObject(RepositoryObject):
    """Mock repository object for testing."""

    id: UUID
    name: str = ""
    count: int = 0
    tags: list[str] = []
    nested: dict[str, Any] = {}

    @property
    def id_(self) -> UUID:
        return self.id


class MockPersister(PersisterBase[MockRepositoryObject]):
    """Mock persister for testing."""

    _mock_repository: BaseRepository[MockRepositoryObject] | None = None

    @classmethod
    def get_repository(cls) -> BaseRepository[MockRepositoryObject]:
        assert cls._mock_repository is not None
        return cls._mock_repository


class MockRepositoryObjectWithComputed(RepositoryObject):
    """Mock repository object with computed fields for testing."""

    id: UUID
    first_name: str = ""
    last_name: str = ""

    @property
    def id_(self) -> UUID:
        return self.id

    @computed_field  # type: ignore[misc]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class MockPersisterWithComputed(PersisterBase[MockRepositoryObjectWithComputed]):
    """Mock persister with computed fields for testing."""

    _mock_repository: BaseRepository[MockRepositoryObjectWithComputed] | None = None

    @classmethod
    def get_repository(cls) -> BaseRepository[MockRepositoryObjectWithComputed]:
        assert cls._mock_repository is not None
        return cls._mock_repository


class TestComputeDirtyFields:
    """Tests for _compute_dirty_fields method."""

    def test_no_changes_returns_empty_set(self):
        """When no fields are modified, dirty set should be empty."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="test", count=5)

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # No modifications
            dirty = persister._compute_dirty_fields()
            assert dirty == set()

    def test_scalar_field_change_detected(self):
        """Scalar field modifications should be detected."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original", count=5)

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # Modify scalar fields
            persister._object.name = "modified"
            persister._object.count = 10

            dirty = persister._compute_dirty_fields()
            assert dirty == {"name", "count"}

    def test_list_mutation_detected(self):
        """List mutations (append/remove) should be detected."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, tags=["a", "b"])

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # Mutate list
            persister._object.tags.append("c")

            dirty = persister._compute_dirty_fields()
            assert dirty == {"tags"}

    def test_list_replacement_detected(self):
        """List replacement should be detected."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, tags=["a", "b"])

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # Replace list
            persister._object.tags = ["x", "y", "z"]

            dirty = persister._compute_dirty_fields()
            assert dirty == {"tags"}

    def test_nested_object_change_marks_parent_dirty(self):
        """Nested object changes should mark the parent field as dirty."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, nested={"key": "value"})

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # Modify nested dict
            persister._object.nested["key"] = "new_value"

            dirty = persister._compute_dirty_fields()
            assert dirty == {"nested"}

    def test_multiple_field_changes_detected(self):
        """Multiple field changes should all be detected."""
        object_id = uuid4()
        obj = MockRepositoryObject(
            id=object_id, name="original", count=1, tags=["a"], nested={"x": 1}
        )

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            # Modify multiple fields
            persister._object.name = "modified"
            persister._object.count = 2
            persister._object.tags.append("b")
            persister._object.nested["y"] = 2

            dirty = persister._compute_dirty_fields()
            assert dirty == {"name", "count", "tags", "nested"}

    def test_computed_field_change_detected(self):
        """Computed field changes should be detected when source fields change."""
        object_id = uuid4()
        obj = MockRepositoryObjectWithComputed(
            id=object_id, first_name="John", last_name="Doe"
        )

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersisterWithComputed._mock_repository = mock_repo

        with MockPersisterWithComputed(object_id) as persister:
            # Modify source field - computed field full_name should also change
            persister._object.first_name = "Jane"

            dirty = persister._compute_dirty_fields()
            # Both the source field and computed field should be dirty
            assert "first_name" in dirty
            assert "full_name" in dirty


class TestPersisterBaseExit:
    """Tests for __exit__ method behavior."""

    def test_no_persist_when_no_changes(self):
        """When no fields changed, update should not be called."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="test")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id):
            pass  # No modifications

        mock_repo.update.assert_not_called()

    def test_update_called_with_dirty_fields(self):
        """When fields change, update should be called with include set."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original", count=5)

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with MockPersister(object_id) as persister:
            persister._object.name = "modified"

        mock_repo.update.assert_called_once_with(obj, include={"name"})

    def test_exception_on_enter_not_persisted(self):
        """When exception occurs in context, update should not be called."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="test")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        MockPersister._mock_repository = mock_repo

        with pytest.raises(ValueError):
            with MockPersister(object_id) as persister:
                persister._object.name = "modified"
                raise ValueError("Test exception")

        mock_repo.update.assert_not_called()

    def test_update_failure_raises_persisting_exception(self):
        """When update fails with ConflictError, PersistingException should be
        raised."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.update.side_effect = ConflictError(
            "version conflict", MagicMock(), None
        )
        MockPersister._mock_repository = mock_repo

        with pytest.raises(PersistingException):
            with MockPersister(object_id) as persister:
                persister._object.name = "modified"
