import pytest
from requests import HTTPError, Response

from worker.services.rspamd_service import (
    RspamdPermanentError,
    RspamdTransientError,
    classify_rspamd_http_error,
)


def _http_error(status_code: int | None) -> HTTPError:
    if status_code is None:
        return HTTPError("no response")
    response = Response()
    response.status_code = status_code
    return HTTPError(f"HTTP {status_code}", response=response)


@pytest.mark.parametrize("status_code", [500, 502, 503, 504, 429, 408])
def test_server_side_statuses_are_transient(status_code: int):
    assert isinstance(
        classify_rspamd_http_error(_http_error(status_code)), RspamdTransientError
    )


@pytest.mark.parametrize("status_code", [400, 403, 404, 405, 413, 415])
def test_refusals_are_permanent(status_code: int):
    assert isinstance(
        classify_rspamd_http_error(_http_error(status_code)), RspamdPermanentError
    )


def test_missing_response_is_transient():
    assert isinstance(
        classify_rspamd_http_error(_http_error(None)), RspamdTransientError
    )
