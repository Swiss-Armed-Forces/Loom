from typing import get_args

import pytest
from requests import HTTPError, Response

from worker.services.tika_service import (
    TikaPermanentError,
    TikaTransientError,
    classify_tika_http_error,
    ocr_languages_for,
)
from worker.settings import TikaAllowedOcrLanguage, TikaCommonOcrLanguage


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


def test_the_options_offered_are_languages_tesseract_has():
    """`ocr_languages_for` appends the guess straight into `X-Tika-OCRLanguage`, so an
    option that is not a tesseract code is an invalid header at runtime, per file."""
    offered = {member.value for member in TikaCommonOcrLanguage}
    assert offered - {TikaCommonOcrLanguage.OTHER.value} <= set(
        get_args(TikaAllowedOcrLanguage)
    )


@pytest.mark.parametrize(
    "inferred, expected",
    [
        # Appended to the configured set, not substituted for it.
        (TikaCommonOcrLanguage.SPA, ["eng", "deu", "fra", "spa"]),
        # Already configured, so the header must not carry it twice: tesseract reads
        # `eng+deu+fra+deu` as a repeated pass over the same traineddata.
        (TikaCommonOcrLanguage.DEU, ["eng", "deu", "fra"]),
        (None, ["eng", "deu", "fra"]),
    ],
)
def test_the_inferred_language_is_appended_once(
    inferred: TikaCommonOcrLanguage | None, expected: list[str]
):
    assert ocr_languages_for(inferred) == expected
