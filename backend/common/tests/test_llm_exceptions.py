import pytest
from httpx import ConnectError
from pydantic_ai.exceptions import (
    ContentFilterError,
    ModelHTTPError,
    UnexpectedModelBehavior,
)

from common.llm.exceptions import (
    LLMError,
    LLMPermanentError,
    LLMTransientError,
    classify_llm_error,
)

MODEL_NAME = "test-model"


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (503, LLMTransientError),
        (429, LLMTransientError),
        (408, LLMTransientError),
        (400, LLMPermanentError),
    ],
)
def test_http_status_decides_whether_asking_again_can_help(
    status_code: int, expected: type[LLMError]
):
    """Both sides of the 500 boundary, and the two 4xx statuses that cross it."""
    error = classify_llm_error(
        ModelHTTPError(status_code=status_code, model_name=MODEL_NAME)
    )
    assert isinstance(error, expected)


def test_unparsable_model_output_is_transient():
    """An answer that did not parse is a sample, and the next attempt re-rolls it."""
    error = classify_llm_error(UnexpectedModelBehavior("could not parse output"))
    assert isinstance(error, LLMTransientError)


def test_content_filter_refusal_is_permanent():
    """A refusal survives resampling, so the verdict on its base class must not."""
    error = classify_llm_error(ContentFilterError("content filter triggered"))
    assert isinstance(error, LLMPermanentError)


def test_unrecognised_exception_is_transient():
    """Same bias as the tika classifier: a wasted budget beats discarding good work."""
    assert isinstance(classify_llm_error(ConnectError("boom")), LLMTransientError)
