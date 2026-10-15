import pytest
from httpx import ConnectError
from pydantic import BaseModel, ValidationError
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
    UserError,
)

from common.llm.exceptions import (
    LLMPermanentError,
    LLMTransientError,
    classify_llm_error,
)

MODEL_NAME = "test-model"


@pytest.mark.parametrize("status_code", [500, 502, 503, 504, 429, 408])
def test_provider_side_statuses_are_transient(status_code: int):
    """A saturated or restarting inference server clears on its own."""
    error = classify_llm_error(
        ModelHTTPError(status_code=status_code, model_name=MODEL_NAME)
    )
    assert isinstance(error, LLMTransientError)


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
def test_rejected_requests_are_permanent(status_code: int):
    """The provider refusing the request means the request is wrong, not the timing."""
    error = classify_llm_error(
        ModelHTTPError(status_code=status_code, model_name=MODEL_NAME)
    )
    assert isinstance(error, LLMPermanentError)


def test_connection_failures_are_transient():
    error = classify_llm_error(
        ModelAPIError(model_name=MODEL_NAME, message="connection refused")
    )
    assert isinstance(error, LLMTransientError)


def test_unparsable_model_output_is_permanent():
    """Retrying an unparsable answer costs an hour of backoff per affected chunk."""
    error = classify_llm_error(UnexpectedModelBehavior("could not parse output"))
    assert isinstance(error, LLMPermanentError)


def test_misconfiguration_is_permanent():
    assert isinstance(classify_llm_error(UserError("no provider")), LLMPermanentError)


def test_usage_limit_is_permanent():
    error = classify_llm_error(UsageLimitExceeded("request limit exceeded"))
    assert isinstance(error, LLMPermanentError)


def test_validation_error_is_permanent():
    class _Output(BaseModel):
        rank: int

    with pytest.raises(ValidationError) as excinfo:
        _Output.model_validate({"rank": "not a number"})

    assert isinstance(classify_llm_error(excinfo.value), LLMPermanentError)


def test_unrecognised_exception_is_transient():
    """Same bias as the tika classifier: a wasted budget beats discarding good work."""
    assert isinstance(classify_llm_error(ConnectError("boom")), LLMTransientError)
