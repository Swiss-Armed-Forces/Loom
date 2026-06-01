import time
from collections.abc import Callable
from uuid import uuid4

from common.dependencies import (
    get_celery_app,
    get_root_task_information_repository,
)
from common.settings import settings
from common.task_object.root_task_information_repository import RootTaskInformation
from worker.periodic.flush_on_idle_task import flush_on_idle_task

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset

FLUSH_ON_IDLE_TIMEOUT = 60


def _poll_until(
    condition: Callable[[], bool],
    timeout: float,
    error_msg: str,
    action: Callable[[], None] | None = None,
    interval: float = 0.5,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if action is not None:
            action()
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError(error_msg)


def _wait_for_flush_to_complete(timeout: float = 120.0):
    _poll_until(
        lambda: get_root_task_information_repository().count() == 0,
        timeout,
        f"Root task count did not reach 0 within {timeout}s",
        action=lambda: get_celery_app()
        .send_task(flush_on_idle_task.name)
        .get(timeout=FLUSH_ON_IDLE_TIMEOUT),
    )


def test_flush_on_idle_clears_root_task_information():
    """Trigger flush_on_idle_task when idle and verify root task info entries are
    flushed."""
    upload_asset("empty_file.txt")

    fetch_files_from_api(
        search_string="*",
        expected_no_of_files=1,
    )

    _wait_for_flush_to_complete()


def test_root_task_count_throttle_pauses_and_resumes_indexing():
    """Exceed throttle_max_root_tasks to trigger the throttle path, trigger
    flush_on_idle_task, and verify the index queue is resumed so new files can still be
    indexed."""
    # Insert threshold+1 fake entries to exceed the root_task_count throttle condition.
    # bulk_save uses ES streaming_bulk so inserting 10k entries is fast.
    # Note: beat may fire flush_on_idle_task during bulk_save (is_idle() returns True
    # for test-process code), so we don't assert the exact count after insertion.
    entries = [
        RootTaskInformation(root_task_id=uuid4(), object_id=uuid4())
        for _ in range(settings.throttle_max_root_tasks + 1)
    ]
    list(get_root_task_information_repository().bulk_save(entries))

    _wait_for_flush_to_complete()

    # Verify the index queue was resumed: a new file can be indexed end-to-end
    upload_asset("empty_file.txt")
    fetch_files_from_api(search_string="*", expected_no_of_files=1)
