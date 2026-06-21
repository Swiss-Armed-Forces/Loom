import pytest
from common.dependencies import get_celery_app
from worker.periodic.throttle_and_flush_lazybytes_task import (
    throttle_and_flush_lazybytes_task,
)

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

GET_TIMEOUT = 60


def test_throttle_and_flush_lazybytes_task_no_op_below_threshold():
    """When lazybytes usage is below the throttle threshold, the task exits early
    without pausing any task groups or flushing anything."""
    get_celery_app().send_task(throttle_and_flush_lazybytes_task.name).get(
        timeout=GET_TIMEOUT
    )
