import logging

from common.dependencies import get_celery_app

from worker.test.infra.test_task import TestTask

logger = logging.getLogger(__name__)
app = get_celery_app()


class AutoRetryTestException(Exception):
    pass


@app.task(
    bind=True,
    base=TestTask,
    autoretry_for=tuple([AutoRetryTestException]),
    max_retries=5,
    retry_backoff=False,
    default_retry_delay=3,
)
def autoretry_test_task(self, fail_count: int) -> int:
    """Fails `fail_count` times then succeeds.

    Returns the number of retries so callers can assert the task was
    actually retried.

    Uses default_retry_delay=3 (3s = binary 11 = two TTL levels in Native
    Delayed Delivery) to reproduce Bug A: BaseTask.__call__ sees two x-death
    entries and raises DeadTask(). Before the fix the task never completes;
    after the fix it retries correctly.

    Regression tests for:
    - KeyError('exchange_type') during autoretry_for retry
    - False DeadTask for tasks arriving via >=2 delayed TTL levels (Bug A)
    """
    if self.request.retries < fail_count:
        raise AutoRetryTestException()
    return self.request.retries
