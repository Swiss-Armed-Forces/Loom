"""The exception types every LLM-backed Celery task retries on.

One hierarchy shared by every task package, split by whether another attempt can
plausibly succeed, so an ``autoretry_for`` entry names the class the code below it
actually raises.
"""

from pydantic import ValidationError
from pydantic_ai.exceptions import (
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
    UserError,
)

# Statuses below 500 that still say "ask again later" rather than "this request is
# wrong". 429 is a rate limit and 408 a server-side timeout; both clear on their own.
LLM_TRANSIENT_STATUS_CODES = frozenset({408, 429})

# Exceptions that describe a property of the request rather than of the provider: a
# model that answered with unparsable output, a misconfigured provider, a usage cap.
# Every attempt reproduces them exactly.
LLM_PERMANENT_EXCEPTIONS: tuple[type[Exception], ...] = (
    UnexpectedModelBehavior,
    UsageLimitExceeded,
    UserError,
    ValidationError,
)


class LLMError(Exception):
    """An LLM call failed."""


class LLMTransientError(LLMError):
    """The provider failed in a way a later attempt may survive.

    A saturated or restarting inference server, a rate limit, a dropped connection. Only
    this type belongs in a task's ``autoretry_for``.
    """


class LLMPermanentError(LLMError):
    """The call will fail the same way however often it is repeated.

    Retrying costs a full backoff budget per attempt and ends in the same place, which
    at indexing scale is multiplied by the chunk count of every affected document.
    """


def classify_llm_error(exc: Exception, message: str = "LLM call failed") -> LLMError:
    """Sort a provider or validation failure into the transient/permanent split.

    An unrecognised exception counts as transient, matching
    ``classify_tika_http_error``: a wasted retry budget is cheaper than discarding work
    that would have succeeded.
    """
    if isinstance(exc, ModelHTTPError):
        if exc.status_code >= 500 or exc.status_code in LLM_TRANSIENT_STATUS_CODES:
            return LLMTransientError(f"{message}: HTTP {exc.status_code}")
        return LLMPermanentError(f"{message}: HTTP {exc.status_code}")
    if isinstance(exc, LLM_PERMANENT_EXCEPTIONS):
        return LLMPermanentError(f"{message}: {type(exc).__name__}")
    # Everything left over, ModelAPIError's connection failures included.
    return LLMTransientError(f"{message}: {type(exc).__name__}")
