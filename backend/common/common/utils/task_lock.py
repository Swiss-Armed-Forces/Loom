import logging
from functools import wraps
from typing import Callable

from common.dependencies import get_redis_client

logger = logging.getLogger(__name__)

TASK_LOCK_KEY_PREFIX = "task_lock"
TASK_LOCK_DEFAULT_TTL_SECONDS = 60 * 10  # 10 min safety TTL (auto-release on crash)


def task_lock(
    ttl_seconds: int = TASK_LOCK_DEFAULT_TTL_SECONDS,
    blocking: bool = True,
):
    """Decorator that ensures a task only ever runs one instance at a time.

    Uses a Redis distributed lock (redis-py lock()) to prevent concurrent
    execution of the decorated function across workers.

    Args:
        ttl_seconds: Safety TTL for the lock. Auto-releases after this duration
            if the holder crashes without calling finally. Should exceed the
            expected maximum task runtime.
        blocking: If True (default), a new instance waits until the lock is
            released, then runs. If False, a new instance returns None immediately
            if the lock is already held (skip behaviour).

    Usage:
        @app.task(bind=True, base=PeriodicTask)
        @task_lock(ttl_seconds=300)
        def my_periodic_task(self):
            ...
    """

    def decorator(func: Callable) -> Callable:
        lock_key = f"{TASK_LOCK_KEY_PREFIX}:{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            redis_client = get_redis_client()
            lock = redis_client.lock(lock_key, timeout=ttl_seconds)
            acquired = lock.acquire(blocking=blocking)
            if not acquired:
                logger.info(
                    "Task %s.%s already running, skipping",
                    func.__module__,
                    func.__qualname__,
                )
                return None
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return wrapper

    return decorator
