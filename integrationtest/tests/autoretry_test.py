import logging

from common.dependencies import get_celery_app

logger = logging.getLogger(__name__)

GET_TIMEOUT = 60


def test_autoretry_task_succeeds_after_failures():
    """Regression test: autoretry_for must not raise KeyError('exchange_type') on retry.

    The task fails twice and succeeds on the 3rd attempt.
    Before the fix: Reject(KeyError('exchange_type')) on 2nd attempt.
    After the fix: task completes successfully.
    """
    get_celery_app().send_task(
        "worker.test.autoretry_test_task.autoretry_test_task",
        args=[2],
    ).get(timeout=GET_TIMEOUT)
