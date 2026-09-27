import pytest
from redis.exceptions import BusyLoadingError
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from common.dependencies import build_redis_retry, build_redis_retry_async


class _Flaky:
    """Callable that raises `error` for the first `failures` calls, then succeeds."""

    def __init__(self, error: Exception, failures: int):
        self._error = error
        self._failures = failures
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self._failures:
            raise self._error
        return "ok"


@pytest.mark.parametrize(
    "error",
    [
        # Raised while Redis loads its RDB snapshot: the port is already open, so the
        # chart's check-redis-ready init container does not cover this window.
        BusyLoadingError("Redis is loading the dataset in memory"),
        RedisConnectionError("connection refused"),
    ],
)
def test_retries_transient_startup_errors(error: Exception):
    flaky = _Flaky(error, failures=2)

    assert build_redis_retry().call_with_retry(flaky, lambda _: None) == "ok"
    assert flaky.calls == 3


def test_does_not_retry_application_errors():
    """A bad command must fail immediately instead of burning the retry budget."""
    flaky = _Flaky(ResponseError("unknown command"), failures=1)

    with pytest.raises(ResponseError):
        build_redis_retry().call_with_retry(flaky, lambda _: None)
    assert flaky.calls == 1


@pytest.mark.asyncio
async def test_async_policy_retries_transient_startup_errors():
    flaky = _Flaky(
        BusyLoadingError("Redis is loading the dataset in memory"), failures=2
    )

    async def do() -> str:
        return flaky()

    async def fail(_: Exception) -> None:
        return None

    assert await build_redis_retry_async().call_with_retry(do, fail) == "ok"
    assert flaky.calls == 3
