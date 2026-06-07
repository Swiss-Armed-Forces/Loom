# pylint: disable=redefined-outer-name
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest
from celery.app.task import Task
from common.dependencies import get_celery_inspect_service

from worker.utils.processing_task import ProcessingTask


@pytest.fixture()
def processing_task() -> ProcessingTask:
    task: Any = MagicMock(spec=ProcessingTask)
    task.name = "test.task"
    return task


def test_retry_when_throttled_forces_countdown_zero(
    processing_task: ProcessingTask,
):
    get_celery_inspect_service().is_throttled.return_value = True

    with patch.object(Task, "retry") as mock_base_retry:
        ProcessingTask.retry(processing_task, exc=ValueError("err"), countdown=30)

    mock_base_retry.assert_called_once_with(
        args=None,
        kwargs=None,
        exc=ANY,
        throw=True,
        eta=None,
        countdown=0,
        max_retries=None,
    )


def test_retry_when_not_throttled_passes_options_through(
    processing_task: ProcessingTask,
):
    get_celery_inspect_service().is_throttled.return_value = False

    exc = ValueError("err")
    with patch.object(Task, "retry") as mock_base_retry:
        ProcessingTask.retry(processing_task, exc=exc, countdown=30, max_retries=5)

    mock_base_retry.assert_called_once_with(
        args=None,
        kwargs=None,
        exc=exc,
        throw=True,
        eta=None,
        countdown=30,
        max_retries=5,
    )
