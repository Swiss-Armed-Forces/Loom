import pytest
from requests import HTTPError, Response

from worker.services.tika_service import (
    TikaPermanentError,
    TikaTransientError,
    classify_tika_http_error,
)


def _http_error(status_code: int | None) -> HTTPError:
    if status_code is None:
        return HTTPError("no response")
    response = Response()
    response.status_code = status_code
    return HTTPError(f"HTTP {status_code}", response=response)


@pytest.mark.parametrize(
    "status_code",
    [500, 502, 503, 504, 429, 408, 301],
)
def test_server_side_statuses_are_transient(status_code: int):
    """A tika that is unwell has to be asked again, not routed around.

    503 in particular is what a saturated fork pool answers, and treating it as a
    property of the document sends PDFs to the strings extractor.
    """
    assert isinstance(
        classify_tika_http_error(_http_error(status_code)), TikaTransientError
    )


@pytest.mark.parametrize("status_code", [400, 405, 415, 422])
def test_refusals_are_permanent(status_code: int):
    """Tika refusing the document itself is reproducible, so retrying only costs
    time."""
    assert isinstance(
        classify_tika_http_error(_http_error(status_code)), TikaPermanentError
    )


def test_missing_response_is_transient():
    """An HTTPError with no response carries no evidence of a permanent refusal."""
    assert isinstance(classify_tika_http_error(_http_error(None)), TikaTransientError)
