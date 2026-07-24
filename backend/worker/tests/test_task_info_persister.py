# pylint: disable=protected-access, redefined-outer-name
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common.models.base_repository import BaseRepository, BulkOperationResult
from common.task_object.task_object import RepositoryTaskObject, TaskRun

from worker.settings import settings
from worker.utils.persister_base import GlobalPersisterWorker
from worker.utils.task_info_persister import (
    TaskInfoPersister,
    _add_failed_task,
    _add_retried_task,
    _add_success_task,
    _get_or_create_task_record,
    _update_state,
)


@pytest.fixture(autouse=True)
def reset_persister_state():
    """Reset the persister state between tests."""
    GlobalPersisterWorker._instances = {}
    yield
    workers = list(GlobalPersisterWorker._instances.values())
    GlobalPersisterWorker._instances = {}
    for worker in workers:
        worker.shutdown()


class MockTaskInfoPersister(TaskInfoPersister[RepositoryTaskObject]):
    """Mock task info persister for testing."""

    _mock_repository: BaseRepository[RepositoryTaskObject] | None = None

    @classmethod
    def get_repository(cls) -> BaseRepository[RepositoryTaskObject]:
        assert cls._mock_repository is not None
        return cls._mock_repository


@pytest.fixture
def repository_task_object():
    return RepositoryTaskObject(id=uuid4(), tasks=[])


def test_update_state(repository_task_object):
    _update_state(repository_task_object, "completed")
    assert repository_task_object.state == "completed"


def test_get_or_create_task_record_creates_new(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"

    assert len(repository_task_object.tasks) == 0

    record = _get_or_create_task_record(repository_task_object, task_id, task_name)

    assert len(repository_task_object.tasks) == 1
    assert repository_task_object.tasks[0] == record
    assert record.task_id == task_id
    assert record.task_name == task_name


def test_get_or_create_task_record_returns_existing(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"

    record1 = _get_or_create_task_record(repository_task_object, task_id, task_name)
    record2 = _get_or_create_task_record(
        repository_task_object, task_id, "different-name"
    )

    assert len(repository_task_object.tasks) == 1
    assert record1 is record2
    assert record2.task_id == task_id
    # Note: task_name is not updated if it already exists in the current implementation
    assert record2.task_name == task_name


def test_add_failed_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
        exception="Error",
    )

    _add_failed_task(repository_task_object, task_run, task_id, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.failed) == 1
    assert record.failed[0] == task_run
    assert len(record.retried) == 0
    assert len(record.succeeded) == 0


def test_add_retried_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )

    _add_retried_task(repository_task_object, task_run, task_id, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.retried) == 1
    assert record.retried[0] == task_run
    assert len(record.failed) == 0
    assert len(record.succeeded) == 0


def test_add_success_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )

    _add_success_task(repository_task_object, task_run, task_id, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.succeeded) == 1
    assert record.succeeded[0] == task_run
    assert len(record.failed) == 0
    assert len(record.retried) == 0


def test_multiple_runs_accumulate(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"

    run1 = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )
    run2 = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=2.0,
    )

    _add_retried_task(repository_task_object, run1, task_id, task_name)
    _add_success_task(repository_task_object, run2, task_id, task_name)

    assert len(repository_task_object.tasks) == 1
    record = repository_task_object.tasks[0]
    assert len(record.retried) == 1
    assert record.retried[0] == run1
    assert len(record.succeeded) == 1
    assert record.succeeded[0] == run2


def test_string_uuid_mismatch(repository_task_object):
    # This test aims to reproduce the bug where task_id might be a string in the record
    # but a UUID is passed to the function.
    task_id = uuid4()

    _get_or_create_task_record(repository_task_object, task_id, "test-task")

    # Now call it with a string version of the same UUID
    _get_or_create_task_record(repository_task_object, str(task_id), "test-task")

    # If they are different, it will be a new record.
    assert (
        len(repository_task_object.tasks) == 1
    ), "Should have found the existing record even with string ID mismatch"


def test_task_info_persister_integration() -> None:
    """Test using TaskInfoPersister class methods."""
    object_id = uuid4()
    obj = RepositoryTaskObject(id=object_id, state="started", tasks=[])

    mock_repo = MagicMock(spec=BaseRepository)
    mock_repo.get_by_id.return_value = obj
    mock_repo.bulk_save.return_value = [
        BulkOperationResult(object_id=object_id, success=True)
    ]
    MockTaskInfoPersister._mock_repository = mock_repo

    persister = MockTaskInfoPersister(object_id)
    task_id = uuid4()
    task_name = "integration-task"
    task_run = TaskRun(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=5.0,
    )

    persister.update_state("processing")
    persister.add_success_task(task_run, task_id, task_name)

    # Wait for worker to process and save
    time.sleep(settings.persister_max_delay + 0.5)

    mock_repo.bulk_save.assert_called()
    saved_objs = mock_repo.bulk_save.call_args[0][0]
    assert len(saved_objs) == 1
    assert saved_objs[0].state == "processing"
    assert len(saved_objs[0].tasks) == 1
    assert saved_objs[0].tasks[0].task_id == task_id
    assert saved_objs[0].tasks[0].succeeded[0] == task_run
