import time

import pytest
from celery.exceptions import TimeoutError as CeleryTimeoutError
from common.dependencies import get_celery_app, get_queues_service
from common.settings import settings
from worker.test.autoretry_test_task import AlwaysFailException

GRAVEYARD_QUEUE = (
    f"{settings.celery_queue_name_prefix}{settings.celery_graveyard_task_name}"
)
ABYSS_QUEUE = f"{settings.celery_queue_name_prefix}{settings.celery_abyss_task_name}"
POLL_TIMEOUT = 0.01
TOTAL_TIMEOUT = 30
NDL_OBSERVE_TIMEOUT = 60
NDL_RESULT_TIMEOUT = 90
NDL_DELAYED_QUEUE_POLL_SLEEP = 0.5


def test_autoretry_exhaustion_does_not_send_to_graveyard_or_abyss():
    """A task whose autoretry_for exception fires every time should exhaust max_retries
    and raise AlwaysFailException cleanly via result.get().

    On each polling timeout we assert graveyard and abyss are still empty — if either
    fills up the task leaked into the dead-letter chain (regression).
    """
    result = get_celery_app().send_task(
        "worker.test.autoretry_test_task.always_fail_autoretry_test_task"
    )

    deadline = time.monotonic() + TOTAL_TIMEOUT
    with pytest.raises(AlwaysFailException):
        while True:
            try:
                result.get(timeout=POLL_TIMEOUT)
            except (TimeoutError, CeleryTimeoutError):
                all_counts = get_queues_service().get_all_queue_message_counts()
                assert (
                    all_counts.get(GRAVEYARD_QUEUE, 0) == 0
                ), f"graveyard non-empty: {all_counts}"
                assert (
                    all_counts.get(ABYSS_QUEUE, 0) == 0
                ), f"abyss non-empty: {all_counts}"
                if time.monotonic() > deadline:
                    pytest.fail(f"Task did not complete within {TOTAL_TIMEOUT}s")


def test_ndl_routes_retry_through_delayed_queue():
    """A task that fails once with countdown > 0 should retry via Native Delayed
    Delivery: the message must appear in a celery_delayed_* queue between failure
    and retry, and the task must ultimately succeed.

    Regression for Bug B (routing key overflow): before the fix, BaseTask.__call__
    did not strip the NDL prefix from delivery_info['routing_key'], so each retry
    prepended another 56-char binary prefix until struct.error was raised (~retry 4).
    """
    qs = get_queues_service()

    # autoretry_test_task uses default_retry_delay=3 (NDL path) and fails
    # fail_count times before succeeding.
    result = get_celery_app().send_task(
        "worker.test.autoretry_test_task.autoretry_test_task",
        args=[1],  # fail_count=1: fails once, retries once via NDL, then succeeds
    )

    # Wait for the message to appear in a celery_delayed_* queue.
    # The worker picks up the task, fails it, and publishes the retry via NDL —
    # the message then sits in celery_delayed_* for ~3 s before being re-delivered.
    observed_in_delayed = False
    deadline = time.monotonic() + NDL_OBSERVE_TIMEOUT
    while time.monotonic() < deadline:
        if qs.get_delayed_queue_message_count() > 0:
            observed_in_delayed = True
            break
        time.sleep(NDL_DELAYED_QUEUE_POLL_SLEEP)

    assert observed_in_delayed, "Task retry never appeared in a celery_delayed_* queue"

    # Task should complete successfully after the NDL round-trip.
    retries = result.get(timeout=NDL_RESULT_TIMEOUT)
    assert retries == 1, f"Expected exactly 1 retry, got {retries}"
