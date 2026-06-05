import logging

from common.dependencies import get_celery_app

logger = logging.getLogger(__name__)

FAIL_COUNT = 3
GET_TIMEOUT = 90  # allow for retry delays (3s each) + processing


def test_autoretry_task_succeeds_after_failures():
    """Regression test: tasks retried via Native Delayed Delivery with a
    non-power-of-2 delay (3s = binary 11 = two TTL levels) must not be
    killed by a false DeadTask detection.

    Before fix (Bug A): BaseTask.__call__ counts two x-death entries from the
    two TTL levels and raises DeadTask — the task permanently fails.
    After fix: retries succeed and .get() returns the retry count (3).
    """
    retries = (
        get_celery_app()
        .send_task(
            "worker.test.autoretry_test_task.autoretry_test_task",
            args=[FAIL_COUNT],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert retries == FAIL_COUNT
