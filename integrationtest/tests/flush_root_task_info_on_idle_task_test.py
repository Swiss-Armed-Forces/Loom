import time
from collections.abc import Callable

import pytest
from common.dependencies import (
    get_celery_app,
    get_root_task_information_repository,
)
from worker.periodic.flush_root_task_info_on_idle_task import (
    flush_root_task_info_on_idle_task,
)

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

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


def _wait_for_root_task_info_flush(timeout: float = 120.0):
    _poll_until(
        lambda: get_root_task_information_repository().count() == 0,
        timeout,
        f"Root task count did not reach 0 within {timeout}s",
        action=lambda: get_celery_app()
        .send_task(flush_root_task_info_on_idle_task.name)
        .get(timeout=FLUSH_ON_IDLE_TIMEOUT),
    )


def test_flush_root_task_info_on_idle_clears_root_task_information():
    """Trigger flush_root_task_info_on_idle_task when the pipeline is idle and verify
    that root task info entries are flushed."""
    upload_asset("empty_file.txt")

    fetch_files_from_api(
        search_string="*",
        expected_no_of_files=1,
    )

    _wait_for_root_task_info_flush()
