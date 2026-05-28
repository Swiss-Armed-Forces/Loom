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
    default_retry_delay=1,
)
def autoretry_test_task(self, fail_count: int):
    """Fails `fail_count` times then succeeds.

    Regression test for: KeyError('exchange_type') during autoretry_for retry.
    """
    if self.request.retries < fail_count:
        raise AutoRetryTestException()
