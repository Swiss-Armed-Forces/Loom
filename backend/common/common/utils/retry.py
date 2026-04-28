import logging
from time import sleep
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

RETRY_DEFAULT_MAX_ATTEMPTS: int = 5
RETRY_DEFAULT_WAIT_S: int = 10


def retry(
    fn: Callable[[], _T],
    max_attempts: int = RETRY_DEFAULT_MAX_ATTEMPTS,
    wait_s: int = RETRY_DEFAULT_WAIT_S,
) -> _T:
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            if attempt < max_attempts:
                logger.warning(
                    "Attempt %d/%d failed (%s). Retrying in %ds...",
                    attempt,
                    max_attempts,
                    exc,
                    wait_s,
                )
                sleep(wait_s)
            else:
                logger.error("All %d attempts failed: %s", max_attempts, exc)
                raise
    raise AssertionError("unreachable")
