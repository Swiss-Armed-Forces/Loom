# pylint: disable=protected-access, redefined-outer-name
import time
from datetime import datetime, timedelta, timezone
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
    task_name = "test-task"

    assert len(repository_task_object.tasks) == 0

    record = _get_or_create_task_record(repository_task_object, "some_name")
    record = _get_or_create_task_record(repository_task_object, task_name)

    assert len(repository_task_object.tasks) == 2
    assert repository_task_object.tasks[1] == record
    assert record.task_name == task_name


def test_add_failed_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
        exception="Error",
    )

    _add_failed_task(repository_task_object, task_run, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.failed) == 1
    assert record.failed[0] == task_run
    assert record.retried is None
    assert record.succeeded is None


def test_add_retried_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )

    _add_retried_task(repository_task_object, task_run, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.retried) == 1
    assert record.retried[0] == task_run
    assert record.failed is None
    assert record.succeeded is None
    assert record.run_count == 1


def test_add_success_task(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"
    task_run = TaskRun(
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )

    _add_success_task(repository_task_object, task_run, task_name)

    record = repository_task_object.tasks[0]
    assert len(record.succeeded) == 1
    assert record.succeeded[0] == task_run
    assert record.failed is None
    assert record.retried is None


def test_multiple_runs_accumulate(repository_task_object):
    task_id = uuid4()
    task_name = "test-task"

    run1 = TaskRun(
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=1.0,
    )
    run2 = TaskRun(
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=2.0,
    )

    _add_retried_task(repository_task_object, run1, task_name)
    _add_success_task(repository_task_object, run2, task_name)

    assert len(repository_task_object.tasks) == 1
    record = repository_task_object.tasks[0]
    assert len(record.retried) == 1
    assert record.retried[0] == run1
    assert len(record.succeeded) == 1
    assert record.succeeded[0] == run2
    assert record.run_count == 2
    assert record.avg_duration == pytest.approx(1.5)


def test_get_or_create_task_record_returns_existing(repository_task_object):
    _get_or_create_task_record(repository_task_object, "test-task")
    _get_or_create_task_record(repository_task_object, "test-task")

    assert len(repository_task_object.tasks) == 1


def _make_run(started_offset_seconds: int, duration: float = 1.0) -> TaskRun:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    started_at = base + timedelta(seconds=started_offset_seconds)
    return TaskRun(
        task_id=uuid4(),
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=duration),
        duration=duration,
    )


def test_eviction_keeps_list_at_max(repository_task_object):
    task_name = "test-task"
    max_runs = settings.max_no_of_persisted_succeeded_tasks

    for i in range(max_runs + 1):
        _add_success_task(repository_task_object, _make_run(i), task_name)

    record = repository_task_object.tasks[0]
    assert len(record.succeeded) == max_runs


def test_eviction_removes_oldest_run(repository_task_object):
    task_name = "test-task"
    oldest = _make_run(0)
    newer = _make_run(1)
    newest = _make_run(2)

    # max_no_of_persisted_succeeded_tasks defaults to 2, so adding 3 evicts oldest
    _add_success_task(repository_task_object, oldest, task_name)
    _add_success_task(repository_task_object, newer, task_name)
    _add_success_task(repository_task_object, newest, task_name)

    record = repository_task_object.tasks[0]
    assert oldest not in record.succeeded
    assert newer in record.succeeded
    assert newest in record.succeeded


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
        task_id=task_id,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration=5.0,
    )

    persister.update_state("processing")
    persister.add_success_task(task_run, task_name)

    # Wait for worker to process and save
    time.sleep(settings.persister_max_delay + 0.5)

    mock_repo.bulk_save.assert_called()
    saved_objs = mock_repo.bulk_save.call_args[0][0]
    assert len(saved_objs) == 1
    assert saved_objs[0].state == "processing"
    assert len(saved_objs[0].tasks) == 1
    assert saved_objs[0].tasks[0].succeeded[0] == task_run
