import threading

from celery.exceptions import Ignore
from common.utils.task_lock import task_lock


def test_basic_execution():
    """Decorated function runs normally and its return value is passed through."""

    @task_lock(ttl_seconds=10, blocking=False)
    def my_task():
        return 42

    assert my_task() == 42


def test_nonblocking_skips_when_held():
    """With blocking=False, a second call returns None immediately if the lock is
    held."""
    first_inside = threading.Event()
    first_may_finish = threading.Event()

    @task_lock(ttl_seconds=10, blocking=False)
    def slow_task():
        first_inside.set()
        first_may_finish.wait(timeout=5)

    t1 = threading.Thread(target=slow_task)
    t1.start()
    first_inside.wait()  # t1 holds the lock

    result = slow_task()  # should skip
    assert result is None

    first_may_finish.set()
    t1.join(timeout=5)


def test_blocking_serializes_concurrent_calls():
    """With blocking=True, concurrent calls execute strictly sequentially."""
    order = []
    first_started = threading.Event()
    first_may_finish = threading.Event()

    @task_lock(ttl_seconds=30, blocking=True)
    def task():
        order.append("start")
        if len(order) == 1:  # first caller holds the lock open
            first_started.set()
            first_may_finish.wait(timeout=5)
        order.append("end")

    t1 = threading.Thread(target=task)
    t1.start()
    first_started.wait()

    t2 = threading.Thread(target=task)
    t2.start()

    first_may_finish.set()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert order == ["start", "end", "start", "end"]


def test_lock_released_on_exception():
    """Lock is released in finally even when the decorated function raises."""
    call_count = []

    @task_lock(ttl_seconds=10, blocking=False)
    def failing_task():
        call_count.append(1)
        raise RuntimeError("boom")

    for _ in range(3):
        try:
            failing_task()
        except RuntimeError:
            pass

    # Each call must have executed the body (3 calls → 3 entries).
    # If the lock leaked after the first exception, subsequent calls would skip
    # (return None without executing the body), leaving fewer than 3 entries.
    assert len(call_count) == 3


def test_lock_released_on_celery_ignore():
    """Lock is released when the decorated function raises celery.exceptions.Ignore,
    which is what self.replace() raises internally in Celery tasks."""
    call_count = []

    @task_lock(ttl_seconds=10, blocking=False)
    def replace_like_task():
        call_count.append(1)
        raise Ignore()

    for _ in range(3):
        try:
            replace_like_task()
        except Ignore:
            pass

    # Each call must have executed the body (3 calls → 3 entries).
    # If the lock leaked on the first Ignore, subsequent calls would skip (return None),
    # which means fewer than 3 body executions.
    assert len(call_count) == 3
