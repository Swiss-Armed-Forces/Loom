import pytest
from celery import Celery

from common.celery_app._base_task import BaseTask

MAX_RETRIES = 3


class _ExampleTask(BaseTask):
    def run(self, *args, **kwargs) -> None:
        pass


def _task(*, max_retries: int | None, retries: int) -> BaseTask:
    """A task bound to an app, standing on its ``retries``-th attempt."""
    task: BaseTask = Celery().register_task(_ExampleTask())
    task.max_retries = max_retries
    task.push_request(retries=retries)
    return task


@pytest.mark.parametrize(
    ("retries", "expected"),
    [
        pytest.param(0, False, id="first-attempt"),
        pytest.param(MAX_RETRIES - 1, False, id="one-retry-left"),
        pytest.param(MAX_RETRIES, True, id="budget-exhausted"),
    ],
)
def test_is_last_attempt_tracks_the_retry_budget(retries: int, expected: bool):
    assert _task(max_retries=MAX_RETRIES, retries=retries).is_last_attempt is expected


def test_is_last_attempt_is_never_reached_when_retries_are_unlimited():
    """``max_retries=None`` means retry forever, so there is no last attempt."""
    assert _task(max_retries=None, retries=1000).is_last_attempt is False
