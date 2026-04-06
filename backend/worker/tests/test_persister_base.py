# pylint: disable=protected-access, too-many-lines
import asyncio
import time
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from common.models.base_repository import (
    BaseRepository,
    BulkOperationResult,
    RepositoryBulkSaveError,
    RepositoryObject,
)
from pydantic import Field

from worker.settings import settings
from worker.utils.persister_base import (
    GlobalPersisterWorker,
    PersisterBase,
    _ObjectMutation,
    _ObjectState,
    mutation,
)


@pytest.fixture(autouse=True)
def reset_persister_state():
    """Reset the persister state between tests."""
    MockPersister._worker = None
    yield
    if MockPersister._worker is None:
        return

    loop = MockPersister._worker._loop
    if loop is None:
        return

    # Cancel all tasks and wait
    async def cleanup():
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        # Wait for cancellation
        await asyncio.gather(*tasks, return_exceptions=True)

    # Run cleanup
    future = asyncio.run_coroutine_threadsafe(cleanup(), loop)
    future.result(timeout=5.0)  # Wait for tasks to cancel

    # Stop loop
    loop.call_soon_threadsafe(loop.stop)

    # Wait for thread
    loop_thread = MockPersister._worker._loop_thread
    if loop_thread:
        loop_thread.join(timeout=2.0)

    # Close loop
    if not loop.is_closed():
        loop.close()


class MockRepositoryObject(RepositoryObject):
    """Mock repository object for testing."""

    id: UUID
    name: str = ""
    count: int = 0
    tags: list[str] = Field(default_factory=list)

    @property
    def id_(self) -> UUID:
        return self.id


# Module-level mutation functions for MockPersister
def _set_name(obj: MockRepositoryObject, name: str) -> None:
    obj.name = name


def _set_count(obj: MockRepositoryObject, count: int) -> None:
    obj.count = count


def _add_tag(obj: MockRepositoryObject, tag: str) -> None:
    obj.tags.append(tag)


class MockPersister(PersisterBase[MockRepositoryObject]):
    """Mock persister for testing."""

    _mock_repository: BaseRepository[MockRepositoryObject] | None = None

    @classmethod
    def get_repository(cls) -> BaseRepository[MockRepositoryObject]:
        assert cls._mock_repository is not None
        return cls._mock_repository

    # Bind mutations as class attributes
    set_name = mutation(_set_name)
    set_count = mutation(_set_count)
    add_tag = mutation(_add_tag)


class TestPersisterBaseSubmit:
    """Tests for submit() method behavior."""

    def test_single_mutation_applied_and_persisted(self) -> None:
        """A single mutation should be applied and persisted."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id, success=True)
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for worker to process and save
        time.sleep(settings.persister_max_delay + 0.5)

        mock_repo.bulk_save.assert_called()
        # Verify the mutation was applied
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert len(saved_objs) == 1
        assert saved_objs[0].name == "modified"

    def test_multiple_mutations_batched(self) -> None:
        """Multiple rapid mutations should be batched and saved together."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original", count=0, tags=[])

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id, success=True)
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")
        persister.set_count(42)
        persister.add_tag("tag1")
        persister.add_tag("tag2")

        # Wait for worker to process and save
        time.sleep(settings.persister_max_delay + 0.5)

        # Should be saved once with all mutations applied
        mock_repo.bulk_save.assert_called_once()
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert len(saved_objs) == 1
        assert saved_objs[0].name == "modified"
        assert saved_objs[0].count == 42
        assert saved_objs[0].tags == ["tag1", "tag2"]

    def test_conflict_error_triggers_reload_and_replay(self) -> None:
        """ConflictError should trigger reload and replay of mutations."""
        object_id = uuid4()
        original_obj = MockRepositoryObject(id=object_id, name="original")
        reloaded_obj = MockRepositoryObject(id=object_id, name="reloaded")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = [original_obj, reloaded_obj]
        # First bulk_save returns conflict, second succeeds
        mock_repo.bulk_save.side_effect = [
            [
                BulkOperationResult(
                    object_id=object_id,
                    success=False,
                    error=RepositoryBulkSaveError("save error"),
                )
            ],
            [BulkOperationResult(object_id=object_id, success=True)],
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for worker to process and save (needs extra time for retry)
        time.sleep(settings.persister_max_delay * 2 + 1.0)

        # Should have called bulk_save twice (first failed, second succeeded)
        assert mock_repo.bulk_save.call_count == 2
        # get_by_id called twice: initial load + reload after conflict
        assert mock_repo.get_by_id.call_count == 2

        # Final saved object should have mutation replayed
        saved_objs = mock_repo.bulk_save.call_args_list[1][0][0]
        assert saved_objs[0].name == "modified"

    def test_max_retries_exceeded_drops_object(self) -> None:
        """Object should be dropped after max retries."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        # Always fail with conflict
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(
                object_id=object_id,
                success=False,
                error=RepositoryBulkSaveError("save error"),
            )
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for worker to process - it will exhaust retries
        time.sleep(
            settings.persister_max_delay * (settings.persister_save_max_retries + 2)
        )

        # Should have attempted SAVE_MAX_RETRIES + 1 times (initial + retries)
        assert mock_repo.bulk_save.call_count == settings.persister_save_max_retries + 1

    def test_object_not_found_on_reload_drops_object(self) -> None:
        """Object should be dropped if not found on reload."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        # First load succeeds, reload returns None
        mock_repo.get_by_id.side_effect = [obj, None]
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(
                object_id=object_id,
                success=False,
                error=RepositoryBulkSaveError("save error"),
            )
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for worker to process
        time.sleep(settings.persister_max_delay + 0.5)

        # Should have tried to save once and then failed on reload
        assert mock_repo.bulk_save.call_count == 1
        assert mock_repo.get_by_id.call_count == 2

    def test_object_not_found_on_initial_load_is_skipped(self) -> None:
        """Mutation for non-existent object is ignored."""
        object_id = uuid4()

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = None
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        time.sleep(settings.persister_max_delay + 0.5)

        # Should have attempted to load but not save (object not found)
        mock_repo.get_by_id.assert_called_once_with(object_id)
        mock_repo.bulk_save.assert_not_called()

    def test_non_conflict_error_logs_and_continues(self) -> None:
        """Generic errors logged, object stays in cache."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        # First save fails with generic error, second succeeds
        mock_repo.bulk_save.side_effect = [
            [
                BulkOperationResult(
                    object_id=object_id,
                    success=False,
                    error=Exception("generic error"),
                )
            ],
            [BulkOperationResult(object_id=object_id, success=True)],
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for first save attempt
        time.sleep(settings.persister_max_delay + 0.5)

        # First bulk_save called with the mutation
        assert mock_repo.bulk_save.call_count == 1

        # Submit another mutation - object should still be in cache
        persister.set_count(42)

        time.sleep(settings.persister_max_delay + 0.5)

        # Second save should succeed, and object should have both mutations
        assert mock_repo.bulk_save.call_count == 2
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert saved_objs[0].name == "modified"
        assert saved_objs[0].count == 42

    def test_conflict_retry_counter_resets_after_success(self) -> None:
        """After successful save, retries reset to 0."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")
        reloaded_obj = MockRepositoryObject(id=object_id, name="reloaded")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = [obj, reloaded_obj, reloaded_obj]

        # Sequence: conflict -> success -> conflict -> success
        mock_repo.bulk_save.side_effect = [
            [
                BulkOperationResult(
                    object_id=object_id,
                    success=False,
                    error=RepositoryBulkSaveError("save error"),
                )
            ],
            [BulkOperationResult(object_id=object_id, success=True)],
            [
                BulkOperationResult(
                    object_id=object_id,
                    success=False,
                    error=RepositoryBulkSaveError("save error"),
                )
            ],
            [BulkOperationResult(object_id=object_id, success=True)],
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("first_change")

        # Wait for first conflict and retry
        time.sleep(settings.persister_max_delay * 2 + 1.0)

        # Reset side_effect for next sequence
        mock_repo.get_by_id.side_effect = [reloaded_obj]

        # Submit another mutation - this should work even after previous conflict
        persister.set_name("second_change")

        time.sleep(settings.persister_max_delay * 2 + 1.0)

        # If retry counter wasn't reset, we'd hit max retries
        # We should have 4 bulk_save calls total (2 per change cycle)
        assert mock_repo.bulk_save.call_count == 4


class TestGlobalPersisterWorker:
    """Tests for GlobalPersisterWorker in isolation."""

    def test_worker_processes_mutations(self) -> None:
        """Worker applies mutations from queue."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id, success=True)
        ]

        worker: GlobalPersisterWorker[MockRepositoryObject] = GlobalPersisterWorker(
            lambda: mock_repo
        )

        def set_name(obj: MockRepositoryObject):
            obj.name = "modified"

        worker.submit(_ObjectMutation(object_id=object_id, mutation_fn=set_name))

        time.sleep(settings.persister_max_delay + 0.5)

        mock_repo.bulk_save.assert_called()
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert saved_objs[0].name == "modified"

    def test_worker_batches_multiple_objects(self) -> None:
        """Multiple objects saved in single bulk_save call."""
        object_id_1 = uuid4()
        object_id_2 = uuid4()
        obj1 = MockRepositoryObject(id=object_id_1, name="obj1")
        obj2 = MockRepositoryObject(id=object_id_2, name="obj2")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = lambda id_: (
            obj1 if id_ == object_id_1 else obj2
        )
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id_1, success=True),
            BulkOperationResult(object_id=object_id_2, success=True),
        ]

        worker: GlobalPersisterWorker[MockRepositoryObject] = GlobalPersisterWorker(
            lambda: mock_repo
        )

        def mutate1(obj: MockRepositoryObject):
            obj.name = "modified1"

        def mutate2(obj: MockRepositoryObject):
            obj.name = "modified2"

        worker.submit(_ObjectMutation(object_id=object_id_1, mutation_fn=mutate1))
        worker.submit(_ObjectMutation(object_id=object_id_2, mutation_fn=mutate2))

        time.sleep(settings.persister_max_delay + 0.5)

        # Should be called once with both objects
        mock_repo.bulk_save.assert_called_once()
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert len(saved_objs) == 2

    def test_worker_handles_conflict_with_reload_replay(self) -> None:
        """ConflictError triggers reload and replay."""
        object_id = uuid4()
        original_obj = MockRepositoryObject(id=object_id, name="original")
        reloaded_obj = MockRepositoryObject(id=object_id, name="reloaded")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = [original_obj, reloaded_obj]
        mock_repo.bulk_save.side_effect = [
            [
                BulkOperationResult(
                    object_id=object_id,
                    success=False,
                    error=RepositoryBulkSaveError("save error"),
                )
            ],
            [BulkOperationResult(object_id=object_id, success=True)],
        ]

        worker: GlobalPersisterWorker[MockRepositoryObject] = GlobalPersisterWorker(
            lambda: mock_repo
        )

        def set_name(obj: MockRepositoryObject):
            obj.name = "modified"

        worker.submit(_ObjectMutation(object_id=object_id, mutation_fn=set_name))

        time.sleep(settings.persister_max_delay * 2 + 1.0)

        assert mock_repo.bulk_save.call_count == 2
        saved_objs = mock_repo.bulk_save.call_args_list[1][0][0]
        assert saved_objs[0].name == "modified"


class TestBulkPersistence:
    """Tests for bulk persistence behavior via PersisterBase."""

    def test_multiple_objects_batched_in_single_bulk_save(self) -> None:
        """Multiple objects mutated should be saved in one bulk call."""
        object_id_1 = uuid4()
        object_id_2 = uuid4()
        obj1 = MockRepositoryObject(id=object_id_1, name="obj1")
        obj2 = MockRepositoryObject(id=object_id_2, name="obj2")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = lambda id_: (
            obj1 if id_ == object_id_1 else obj2
        )
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id_1, success=True),
            BulkOperationResult(object_id=object_id_2, success=True),
        ]
        MockPersister._mock_repository = mock_repo

        persister1 = MockPersister(object_id_1)
        persister2 = MockPersister(object_id_2)

        persister1.set_name("modified1")
        persister2.set_name("modified2")

        time.sleep(settings.persister_max_delay + 0.5)

        # Should be called once with both objects
        mock_repo.bulk_save.assert_called_once()
        saved_objs = mock_repo.bulk_save.call_args[0][0]
        assert len(saved_objs) == 2

    def test_partial_failure_doesnt_block_successful_saves(self) -> None:
        """If one object fails, others should still succeed."""
        object_id_1 = uuid4()
        object_id_2 = uuid4()
        obj1 = MockRepositoryObject(id=object_id_1, name="obj1")
        obj2 = MockRepositoryObject(id=object_id_2, name="obj2")
        reloaded_obj1 = MockRepositoryObject(id=object_id_1, name="obj1_reloaded")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.side_effect = [obj1, obj2, reloaded_obj1]
        mock_repo.bulk_save.side_effect = [
            [
                BulkOperationResult(
                    object_id=object_id_1,
                    success=False,
                    error=RepositoryBulkSaveError("save error"),
                ),
                BulkOperationResult(object_id=object_id_2, success=True),
            ],
            [BulkOperationResult(object_id=object_id_1, success=True)],
        ]
        MockPersister._mock_repository = mock_repo

        persister1 = MockPersister(object_id_1)
        persister2 = MockPersister(object_id_2)

        persister1.set_name("modified1")
        persister2.set_name("modified2")

        time.sleep(settings.persister_max_delay * 2 + 1.0)

        # First call has both, second call only has the retried one
        assert mock_repo.bulk_save.call_count == 2

    def test_object_cached_after_successful_save(self) -> None:
        """Objects stay cached after successful save to avoid repeated loads."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id, success=True)
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        time.sleep(settings.persister_max_delay + 0.5)

        # Object should be saved
        mock_repo.bulk_save.assert_called_once()
        assert mock_repo.get_by_id.call_count == 1

        # Submit another mutation - should NOT trigger a new get_by_id (object cached)
        mock_repo.get_by_id.reset_mock()
        persister.set_name("modified_again")

        time.sleep(settings.persister_max_delay + 0.5)

        # Object should still be cached, no new load needed
        mock_repo.get_by_id.assert_not_called()
        # But it should have been saved again
        assert mock_repo.bulk_save.call_count == 2


class TestStaleObjectCleanup:
    """Tests for stale object cleanup behavior."""

    def test_stale_objects_forgotten_after_timeout(self) -> None:
        """Objects removed after FORGET_MULTIPLIER * MAX_DELAY."""
        object_id = uuid4()
        obj = MockRepositoryObject(id=object_id, name="original")

        mock_repo = MagicMock(spec=BaseRepository)
        mock_repo.get_by_id.return_value = obj
        mock_repo.bulk_save.return_value = [
            BulkOperationResult(object_id=object_id, success=True)
        ]
        MockPersister._mock_repository = mock_repo

        persister = MockPersister(object_id)
        persister.set_name("modified")

        # Wait for save
        time.sleep(settings.persister_max_delay + 0.5)
        assert mock_repo.bulk_save.call_count == 1
        mock_repo.get_by_id.reset_mock()

        # Wait for forget timeout
        forget_timeout = (
            settings.persister_max_delay
            * settings.persister_max_delay_forget_multiplier
        )
        time.sleep(forget_timeout + 1.0)

        # Now submit another mutation - should require a fresh load
        persister.set_name("after_forget")

        time.sleep(settings.persister_max_delay + 0.5)

        # Object should have been forgotten and reloaded
        mock_repo.get_by_id.assert_called_once_with(object_id)


class TestObjectState:
    """Tests for _ObjectState mutation tracking and encapsulation."""

    def test_init_sets_state_correctly(self) -> None:
        """Constructor should initialize state correctly."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        assert state.obj is obj
        assert state.last_update_ts == 1.0
        assert state.first_update_ts is None
        assert state.recovery_attempts == 0
        assert not state.has_pending_mutations

    def test_obj_property_is_readonly(self) -> None:
        """Obj property should return the internal object."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        assert state.obj is obj
        # Note: We can't easily test that assignment fails at runtime
        # since Python doesn't enforce this, but the property has no setter

    def test_apply_mutation_modifies_object(self) -> None:
        """apply_mutation should apply the mutation function to the object."""
        obj = MockRepositoryObject(id=uuid4(), name="original")
        state = _ObjectState(obj=obj, now=1.0)

        def set_name(o: MockRepositoryObject) -> None:
            o.name = "modified"

        state.apply_mutation(set_name, now=2.0)

        assert state.obj.name == "modified"

    def test_apply_mutation_records_in_replay_log(self) -> None:
        """apply_mutation should record mutation for potential replay."""
        obj = MockRepositoryObject(id=uuid4(), name="original")
        state = _ObjectState(obj=obj, now=1.0)

        assert not state.has_pending_mutations

        def set_name(o: MockRepositoryObject) -> None:
            o.name = "modified"

        state.apply_mutation(set_name, now=2.0)

        assert state.has_pending_mutations

    def test_apply_mutation_updates_timestamps(self) -> None:
        """apply_mutation should update last_update_ts and first_update_ts."""
        obj = MockRepositoryObject(id=uuid4(), name="original")
        state = _ObjectState(obj=obj, now=1.0)

        assert state.first_update_ts is None

        def mutation1(o: MockRepositoryObject) -> None:
            o.name = "first"

        state.apply_mutation(mutation1, now=2.0)

        assert state.last_update_ts == 2.0
        assert state.first_update_ts == 2.0

        def mutation2(o: MockRepositoryObject) -> None:
            o.name = "second"

        state.apply_mutation(mutation2, now=3.0)

        assert state.last_update_ts == 3.0
        assert state.first_update_ts == 2.0  # Should not change

    def test_set_obj_replaces_object(self) -> None:
        """set_obj should replace the internal object."""
        obj1 = MockRepositoryObject(id=uuid4(), name="original")
        obj2 = MockRepositoryObject(id=uuid4(), name="replacement")
        state = _ObjectState(obj=obj1, now=1.0)

        state.replace_obj(obj2, now=2.0)

        assert state.obj is obj2

    def test_set_obj_replays_mutations(self) -> None:
        """set_obj should replay all pending mutations on the new object."""
        obj1 = MockRepositoryObject(id=uuid4(), name="original", count=0)
        state = _ObjectState(obj=obj1, now=1.0)

        # Apply some mutations
        state.apply_mutation(lambda o: setattr(o, "name", "modified"), now=2.0)
        state.apply_mutation(lambda o: setattr(o, "count", 42), now=2.5)

        # Replace with fresh object
        obj2 = MockRepositoryObject(id=uuid4(), name="fresh", count=0)
        state.replace_obj(obj2, now=3.0)

        # Mutations should have been replayed
        assert state.obj.name == "modified"
        assert state.obj.count == 42

    def test_set_obj_updates_timestamps(self) -> None:
        """set_obj should update both timestamps to trigger a new save."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)
        # Simulate previous mutation to set first_update_ts
        state.apply_mutation(lambda o: None, now=0.5)
        assert state.first_update_ts == 0.5

        new_obj = MockRepositoryObject(id=uuid4(), name="new")
        state.replace_obj(new_obj, now=5.0)

        assert state.first_update_ts == 5.0
        assert state.last_update_ts == 5.0

    def test_mark_saved_clears_replay_log(self) -> None:
        """mark_saved should clear pending mutations."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        state.apply_mutation(lambda o: setattr(o, "name", "modified"), now=2.0)
        assert state.has_pending_mutations

        state.mark_saved()

        assert not state.has_pending_mutations

    def test_mark_saved_clears_first_update_ts(self) -> None:
        """mark_saved should reset first_update_ts to None."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        state.apply_mutation(lambda o: setattr(o, "name", "modified"), now=2.0)
        assert state.first_update_ts == 2.0

        state.mark_saved()

        assert state.first_update_ts is None

    def test_increment_recovery_attempts(self) -> None:
        """increment_recovery_attempts should increment the counter."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        assert state.recovery_attempts == 0

        state.increment_recovery_attempts()
        assert state.recovery_attempts == 1

        state.increment_recovery_attempts()
        assert state.recovery_attempts == 2

        state.increment_recovery_attempts()
        assert state.recovery_attempts == 3

    def test_replace_obj_does_not_increment_counter(self) -> None:
        """replace_obj should not auto-increment recovery_attempts."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        assert state.recovery_attempts == 0

        state.replace_obj(MockRepositoryObject(id=uuid4(), name="v1"), now=2.0)
        assert state.recovery_attempts == 0  # Counter not incremented by replace_obj

    def test_mark_saved_resets_recovery_attempts(self) -> None:
        """mark_saved should reset recovery_attempts to zero."""
        obj = MockRepositoryObject(id=uuid4(), name="test")
        state = _ObjectState(obj=obj, now=1.0)

        # Simulate some recovery attempts
        state.increment_recovery_attempts()
        state.increment_recovery_attempts()
        assert state.recovery_attempts == 2

        state.mark_saved()

        assert state.recovery_attempts == 0
