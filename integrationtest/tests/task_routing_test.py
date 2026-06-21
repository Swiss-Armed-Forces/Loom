import logging
import time
from contextlib import contextmanager
from typing import Generator

import pytest
from common.dependencies import get_celery_app, get_queues_service

from utils.settings import settings

logger = logging.getLogger(__name__)

FAIL_COUNT = 3
GET_TIMEOUT = 90  # allow for retry delays (3s × FAIL_COUNT=3) + processing

_UNROUTABLE_QUEUE = (
    f"{settings.celery_queue_name_prefix}{settings.celery_unroutable_task_name}"
)

_POLL_INTERVAL = 0.5
_POLL_TIMEOUT = 10


@pytest.fixture(autouse=True)
def ensure_unroutable_queue_empty() -> Generator[None, None, None]:
    """Wait for loom:unroutable to be empty before each test.

    The global wipe_data fixture purges all queues between tests, but the RabbitMQ
    management API lags slightly. Polling here ensures the count has settled to zero
    before any assertion is made.
    """
    deadline = time.monotonic() + _POLL_TIMEOUT
    while time.monotonic() < deadline:
        if get_queues_service().get_message_count(queue_name=_UNROUTABLE_QUEUE) == 0:
            break
        time.sleep(_POLL_INTERVAL)
    yield


@contextmanager
def assert_unroutable_queue_unchanged() -> Generator[None, None, None]:
    """Context manager that asserts no messages leak into the unroutable queue."""
    yield
    count = get_queues_service().get_message_count(queue_name=_UNROUTABLE_QUEUE)
    assert count == 0, (
        f"Unroutable queue contains {count} message(s); "
        "delayed retries are leaking to loom:unroutable"
    )


@contextmanager
def assert_unroutable_has_one_message(task_name: str) -> Generator[None, None, None]:
    """Context manager that asserts loom:unroutable reaches exactly one message."""
    yield
    deadline = time.monotonic() + _POLL_TIMEOUT
    count = 0
    while time.monotonic() < deadline:
        count = get_queues_service().get_message_count(queue_name=_UNROUTABLE_QUEUE)
        if count == 1:
            break
        time.sleep(_POLL_INTERVAL)
    assert count == 1, (
        f"Expected loom:unroutable to contain 1 message, got {count} "
        f"after sending {task_name!r}. Alternate-exchange routing may be broken."
    )


def test_autoretry_task_succeeds_after_failures():
    """Regression test for two autoretry bugs:

    Bug A — false DeadTask detection:
        A 3s countdown traverses two TTL levels (binary 11), producing two
        x-death entries. Before the fix, BaseTask.__call__ counted those
        entries and raised DeadTask; the task permanently failed.

    Bug B — unroutable queue leak:
        DelayedDelivery._bind_queues processes the unroutable queue
        (routing_key="*") and binds ae-loom -> celery_delayed_delivery with
        "#.*". Since "#.*" matches every task routing key's final segment,
        all delayed retry messages are duplicated into loom:unroutable.
        assert_unroutable_queue_unchanged() catches any such leak.
    """
    with assert_unroutable_queue_unchanged():
        retries = (
            get_celery_app()
            .send_task(
                "worker.test.autoretry_test_task.autoretry_test_task",
                args=[FAIL_COUNT],
            )
            .get(timeout=GET_TIMEOUT)
        )

    assert retries == FAIL_COUNT


@pytest.mark.parametrize(
    "task_name",
    [
        # Single-word key: the original case that worked even with the old topic exchange
        "unroutable_sentinel",
        # Dotted key: realistic Celery task name; was silently dropped when ae-loom
        # was a topic exchange with routing_key="*" — fixed by switching to fanout
        "worker.nonexistent.task.nonexistent_task",
    ],
)
def test_unroutable_messages_land_in_unroutable_queue(task_name: str) -> None:
    """Messages with no matching binding on the loom exchange are forwarded to ae-loom
    (fanout alternate exchange) and delivered to loom:unroutable, regardless of whether
    the routing key is a single word or a dotted task name."""
    with assert_unroutable_has_one_message(task_name):
        # routing_key must be set explicitly — without it Celery falls back to
        # task_default_routing_key which IS a bound queue, so the message would
        # reach a worker, fail as NotRegistered, and dead-letter to abyss.
        get_celery_app().send_task(task_name, routing_key=task_name)
