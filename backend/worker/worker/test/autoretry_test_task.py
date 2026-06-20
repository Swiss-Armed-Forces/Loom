import logging

from common.dependencies import get_celery_app
from common.settings import settings

from worker.test.infra.test_task import TestTask

logger = logging.getLogger(__name__)
app = get_celery_app()


class AutoRetryTestException(Exception):
    pass


@app.task(
    bind=True,
    base=TestTask,
    autoretry_for=(AutoRetryTestException,),
    max_retries=5,
    retry_backoff=False,
    default_retry_delay=3,
)
def autoretry_test_task(self: TestTask, fail_count: int) -> int:
    """Fails `fail_count` times then succeeds.

    Returns the number of retries so callers can assert the task was
    actually retried.

    Uses default_retry_delay=3 (3s = binary 11 = two TTL levels in Native
    Delayed Delivery) to keep the test fast while still exercising Bug A
    and Bug B regressions.

    Regression tests for:
    - KeyError('exchange_type') during autoretry_for retry
    - False DeadTask for tasks arriving via >=2 delayed TTL levels (Bug A)
    - Spurious copies landing in loom:unroutable on every delayed retry (Bug B)
    """
    if self.request.retries < fail_count:
        raise AutoRetryTestException()
    return self.request.retries


@app.task(
    bind=True,
    base=TestTask,
    autoretry_for=(AutoRetryTestException,),
    max_retries=1,
    retry_backoff=False,
    default_retry_delay=30,
)
def ndl_observation_test_task(self: TestTask, fail_count: int) -> int:
    """Fails `fail_count` times then succeeds, with a 30s retry delay.

    Uses default_retry_delay=30 (30s = binary 11110 = 4 TTL levels in Native
    Delayed Delivery: celery_delayed_1=2s, _2=4s, _3=8s, _4=16s) to give the
    RabbitMQ Management API poll loop a wide observation window (~16s in the
    largest level) to confirm the message sits in a celery_delayed_* queue.
    """
    if self.request.retries < fail_count:
        raise AutoRetryTestException()
    return self.request.retries


class AlwaysFailException(Exception):
    pass


@app.task(
    base=TestTask,
    autoretry_for=(AlwaysFailException,),
    max_retries=settings.celery_deliver_limit + 1,
    default_retry_delay=1,
)
def always_fail_autoretry_test_task() -> None:
    """Always raises AlwaysFailException; verifies autoretry exhaustion does not leak
    to the graveyard.

    Covers two related NDL bugs fixed in BaseTask.__call__:

    Bug A — x-death accumulation:
      Celery's retry() copies self.request.headers — including any x-death entries —
      into each new retry message.  Each NDL round-trip (countdown > 0) appends a
      celery_delayed_N entry to x-death.  After enough retries the accumulated x-death
      causes RabbitMQ to route the message to the graveyard before max_retries is
      exhausted.
      Fix: strip celery_delayed_* entries from headers before calling run().

    Bug B — routing key overflow:
      retry() → signature_from_request() copies delivery_info['routing_key'] (the
      NDL-prefixed key, 56 chars longer than the original) into the next retry's
      options.  celery/app/base.py then calls calculate_routing_key() on that
      already-prefixed key, prepending yet another 56-char binary prefix.  After ~4
      retries the routing key exceeds AMQP's 255-byte shortstr limit and a
      struct.error prevents the retry from being published at all.
      Fix: strip the NDL prefix from delivery_info['routing_key'] before calling run().

    Uses default_retry_delay=1 (NDL path) and max_retries = celery_deliver_limit + 1
    to keep the test quick while exceeding the old delivery limit — the scenario that
    previously reproduced both bugs.
    """
    raise AlwaysFailException("always fails")
