import logging
import time

import pytest
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_storage_service,
)
from worker.periodic.flush_file_storage_service_task import (
    flush_file_storage_service_task,
)
from worker.periodic.tasks.flush_file_storage_service import (
    search_and_remove_file_storage_object,
)

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

_TASK_TIMEOUT = 60
_SUBTASK_POLL_TIMEOUT = 30
_SUBTASK_POLL_INTERVAL = 1


class TestFlushFileStorageServiceTask:
    def test_orphaned_object_is_removed(self):
        """An orphaned file storage object (not referenced by any repository) is
        deleted."""
        file_storage = get_file_storage_service()
        lazy = file_storage.from_bytes(b"orphaned content that nobody references")
        assert lazy.service_id is not None
        service_id = str(lazy.service_id)

        get_celery_app().send_task(
            search_and_remove_file_storage_object.name,
            kwargs={"service_id": service_id},
        ).get(timeout=_TASK_TIMEOUT)

        with pytest.raises(Exception, match="."):
            with file_storage.load_memoryview(lazy) as memory:
                _ = bytes(memory)

    def test_referenced_object_is_preserved(self):
        """A file storage object referenced by a repository entry is not deleted."""
        upload_asset("text.txt")
        files = fetch_files_from_api(search_string="*", expected_no_of_files=1)
        file_id = files.files[0].file_id

        file_repository = get_file_repository()
        file = file_repository.get_by_id(file_id)
        assert file is not None
        assert file.storage_data is not None
        assert file.storage_data.service_id is not None
        service_id = str(file.storage_data.service_id)

        get_celery_app().send_task(
            search_and_remove_file_storage_object.name,
            kwargs={"service_id": service_id},
        ).get(timeout=_TASK_TIMEOUT)

        file_storage = get_file_storage_service()
        with file_storage.load_memoryview(file.storage_data) as memory:
            assert len(memory) > 0

    def test_flush_task_removes_orphaned_object(self):
        """flush_file_storage_service_task dispatches removal of orphaned objects.

        Uses min_age_seconds=0 to bypass the age filter so freshly created objects are
        eligible for removal.
        """
        file_storage = get_file_storage_service()
        lazy = file_storage.from_bytes(b"orphaned content for flush task test")
        assert lazy.service_id is not None

        get_celery_app().send_task(
            flush_file_storage_service_task.name,
            kwargs={"min_age_seconds": 0, "start_after_service_id": ""},
        ).get(timeout=_TASK_TIMEOUT)

        # The flush task dispatches subtasks with .forget() — poll until the object is
        # deleted rather than sleeping a fixed amount.
        deadline = time.monotonic() + _SUBTASK_POLL_TIMEOUT
        while time.monotonic() < deadline:
            try:
                with file_storage.load_memoryview(lazy) as memory:
                    _ = bytes(memory)
            except Exception:  # pylint: disable=broad-exception-caught
                break  # object was deleted as expected
            time.sleep(_SUBTASK_POLL_INTERVAL)
        else:
            pytest.fail(
                f"Orphaned object {lazy.service_id} was not removed within "
                f"{_SUBTASK_POLL_TIMEOUT}s"
            )

    def test_flush_task_respects_min_age(self):
        """flush_file_storage_service_task does not remove objects younger than
        min_age."""
        file_storage = get_file_storage_service()
        lazy = file_storage.from_bytes(b"orphaned content that is too young to remove")
        assert lazy.service_id is not None

        # min_age_seconds is set large enough that a freshly created object is not
        # eligible (cutoff = now - min_age is far in the past).
        get_celery_app().send_task(
            flush_file_storage_service_task.name,
            kwargs={"min_age_seconds": 9999},
        ).get(timeout=_TASK_TIMEOUT)

        with file_storage.load_memoryview(lazy):
            pass  # object is still accessible — not removed due to min_age cutoff
