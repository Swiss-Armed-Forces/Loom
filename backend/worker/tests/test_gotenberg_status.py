import pytest
from httpx import HTTPStatusError, Request, Response

from worker.index_file.tasks.render import (
    GotenbergError,
    handle_gotenberg_status_error,
)

MESSAGE = "Unable to render pdf in browser"


def _status_error(status_code: int) -> HTTPStatusError:
    request = Request("POST", "http://gotenberg.loom/forms/chromium/convert/html")
    response = Response(status_code, request=request)
    return HTTPStatusError(f"HTTP {status_code}", request=request, response=response)


@pytest.mark.parametrize("status_code", [503, 502, 429, 408])
def test_capacity_signals_trigger_a_retry(status_code: int):
    """503 is what a saturated Chromium and LibreOffice pool answers.

    Swallowing it recorded "this document has no rendered PDF" for a document that
    renders perfectly well once the pool drains.
    """
    with pytest.raises(GotenbergError):
        handle_gotenberg_status_error(_status_error(status_code), MESSAGE)


@pytest.mark.parametrize("status_code", [400, 403, 404, 415, 504])
def test_refusals_degrade_without_retrying(status_code: int):
    """Gotenberg refusing the document is reproducible, so there is nothing to retry."""
    handle_gotenberg_status_error(_status_error(status_code), MESSAGE)


def test_failed_conversion_degrades_without_retrying():
    """A 500 on a document's own route is a verdict on the document, not on capacity.

    Gotenberg answers 500 with "supervisor run task: uno exception" for a file
    LibreOffice cannot open - an RTF body carved out of a PST, for one. Retrying that
    held the file out of the index for the whole backoff budget and never changed the
    answer.
    """
    handle_gotenberg_status_error(_status_error(500), MESSAGE)


def test_refusal_is_logged(caplog: pytest.LogCaptureFixture):
    with caplog.at_level("WARNING"):
        handle_gotenberg_status_error(_status_error(415), MESSAGE)

    assert MESSAGE in caplog.text
