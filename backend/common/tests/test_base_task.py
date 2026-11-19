from datetime import datetime

import pytest
from celery import Celery

from common.celery_app._base_task import BaseTask
from common.celery_app._dead_letter import DeadTask
from common.settings import settings

MAX_RETRIES = 3

_GRAVEYARD_QUEUE = (
    f"{settings.celery_queue_name_prefix}{settings.celery_graveyard_task_name}"
)


class _ExampleTask(BaseTask):
    def run(self, *args, **kwargs) -> None:
        pass

    @property
    def started_at(self) -> datetime:
        """The stamp ``ProcessingTask.on_failure`` builds its TaskRun from."""
        return self._start_time


def _task(*, max_retries: int | None, retries: int) -> BaseTask:
    """A task bound to an app, standing on its ``retries``-th attempt."""
    task: BaseTask = Celery().register_task(_ExampleTask())
    task.max_retries = max_retries
    task.push_request(retries=retries)
    return task


def _dead_task() -> _ExampleTask:
    """A task holding the x-death of a message dead-lettered out of the graveyard."""
    task: _ExampleTask = Celery().register_task(_ExampleTask())
    task.push_request(
        headers={
            "x-death": [
                {
                    "queue": _GRAVEYARD_QUEUE,
                    "reason": "delivery_limit",
                    "count": 1,
                    "exchange": settings.celery_default_exchange_name,
                    "routing-keys": [settings.celery_graveyard_task_name],
                }
            ]
        }
    )
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


def test_a_dead_task_is_stamped_before_it_is_rejected():
    """Rejecting a dead task runs the failure handlers, which read the stamp.

    Unstamped, ``ProcessingTask.on_failure`` raises AttributeError, celery reports an
    internal error in its place, and the file the dead task belonged to is never moved
    to "failed" — it keeps a non-terminal state no worker will resolve.
    """
    task = _dead_task()

    with pytest.raises(DeadTask):
        task()

    assert task.started_at is not None
