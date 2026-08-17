"""Generic polling utility for integration tests."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def poll_until(
    fetch: Callable[[], T],
    predicate: Callable[[T], bool],
    timeout: float = 30,
    interval: float = 1,
    description: str = "condition",
) -> T:
    """Poll *fetch* until *predicate* returns ``True``, then return the last fetched
    value.

    Raises ``AssertionError`` if *timeout* seconds elapse without the predicate becoming
    true.
    """
    deadline = time.monotonic() + timeout
    result = fetch()
    while not predicate(result):
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"Timed out after {timeout}s waiting for {description}. "
                f"Last value: {result}"
            )
        time.sleep(interval)
        result = fetch()
    return result
