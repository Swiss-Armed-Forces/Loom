import logging
from typing import cast
from unittest.mock import MagicMock

import pytest
from common.file.file_repository import File, FilePurePath
from common.llm.exceptions import LLMTransientError
from common.services.lazybytes_service import InMemoryTempLazyBytesService
from pydantic_ai.exceptions import ModelHTTPError

from worker.dependencies import (
    get_llm_ocr_language_detection_so_agent,
    get_tika_service,
)
from worker.index_file.extractor.unar_extractor import UnarExtractor
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.tika_processing import (
    FALLBACKS,
    TIKA_RETRY_EXCEPTIONS,
    InferredOcrLanguage,
    TikaExtractorFallback,
    TikaProcessingResult,
    choose_tika_processing_result_task,
    infer_language_via_llm_task,
    tika_processor_task,
)
from worker.services.tika_service import (
    TikaPermanentError,
    TikaResult,
    TikaTransientError,
)
from worker.settings import TikaCommonOcrLanguage

PDF_CONTENT_TYPE = "application/pdf"
FORCED_FALLBACK_CONTENT_TYPE = "application/vnd.ms-outlook"

# pylint: disable=redefined-outer-name


def _bound_task(*, is_last_attempt: bool) -> FileIndexingTask:
    """Stand in for the ``self`` of a bound task.

    ``BaseTask.is_last_attempt`` reads the live retry state, which only exists inside a
    worker, so the attribute is set directly here -- the same approach as
    ``test_rag_tool``.
    """
    task = MagicMock(spec=FileIndexingTask)
    task.is_last_attempt = is_last_attempt
    return cast(FileIndexingTask, task)


def _inferred(
    file_type: str = PDF_CONTENT_TYPE,
    language: TikaCommonOcrLanguage | None = None,
) -> InferredOcrLanguage:
    return InferredOcrLanguage(file_type, language)


def _file() -> File:
    return File(
        full_name=FilePurePath("report.pdf"),
        source="api-upload",
        sha256="abc123",
        size=42,
    )


@pytest.fixture()
def tika_service() -> MagicMock:
    """The MagicMock(spec=TikaService) that mock_init installed as the global."""
    return cast(MagicMock, get_tika_service())


@pytest.fixture()
def ocr_language_agent() -> MagicMock:
    """The MagicMock(spec=Agent) that mock_init installed as the OCR language agent."""
    agent = cast(MagicMock, get_llm_ocr_language_detection_so_agent())
    agent.run_sync.return_value = MagicMock(output=TikaCommonOcrLanguage.DEU)
    return agent


def test_parsed_document_is_handled_by_tika(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    tika_service.parse_from_generator.return_value = TikaResult()
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False), _inferred(), content, _file()
    )

    assert result.handled_by == "tika_processor"
    assert result.result is not None
    assert not result.exceptions
    assert not result.degradation_reasons


def test_forced_fallback_content_type_never_reaches_tika(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """These types have dedicated extractors, so tika is skipped rather than failed."""
    content = lazybytes_service_inmemory.from_bytes(data=b"anything")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False),
        _inferred(FORCED_FALLBACK_CONTENT_TYPE),
        content,
        _file(),
    )

    assert result.result is None
    assert not result.exceptions
    tika_service.parse_from_generator.assert_not_called()


def test_transient_failure_is_raised_while_retries_remain(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """A tika 5xx must reach autoretry_for, not the fallbacks.

    Degrading here indexes PDFs as raw byte sequences whenever tika is busy.
    """
    tika_service.parse_from_generator.side_effect = TikaTransientError("HTTP 503")
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    with pytest.raises(TikaTransientError):
        tika_processor_task(
            _bound_task(is_last_attempt=False), _inferred(), content, _file()
        )


def test_transient_failure_degrades_once_the_budget_is_spent(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    caplog: pytest.LogCaptureFixture,
):
    tika_service.parse_from_generator.side_effect = TikaTransientError("HTTP 503")
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    with caplog.at_level(logging.WARNING):
        result = tika_processor_task(
            _bound_task(is_last_attempt=True), _inferred(), content, _file()
        )

    assert result.result is None
    assert result.handled_by is None
    assert len(result.exceptions) == 1
    assert result.degradation_reasons == [
        "tika_processor (retries exhausted): TikaTransientError: HTTP 503"
    ]
    assert "degrading to the fallback extractors" in caplog.text


def test_permanent_failure_degrades_on_the_first_attempt(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """A document tika refuses fails identically every time.

    Spending the full backoff budget on it would occupy a worker for about an hour per
    file before reaching the same answer.
    """
    tika_service.parse_from_generator.side_effect = TikaPermanentError("HTTP 422")
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False), _inferred(), content, _file()
    )

    assert result.result is None
    assert len(result.exceptions) == 1


def test_unforeseen_exception_degrades_rather_than_failing_the_file(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    tika_service.parse_from_generator.side_effect = ValueError("boom")
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False), _inferred(), content, _file()
    )

    assert result.result is None
    assert len(result.exceptions) == 1


def test_only_transient_failures_are_declared_retryable():
    """The invariant the retry classification rests on, and one a refactor breaks
    quietly."""
    assert TikaTransientError in TIKA_RETRY_EXCEPTIONS
    assert TikaPermanentError not in TIKA_RETRY_EXCEPTIONS


def test_unar_is_the_last_fallback():
    """`unar` also reads zip, tar, gzip and xz, so its position is what stops it taking
    files the format-specific extractors above it already handle."""
    assert isinstance(FALLBACKS[-1], TikaExtractorFallback)
    assert isinstance(FALLBACKS[-1].extractor, UnarExtractor)


def test_last_resort_fallback_is_announced(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    caplog: pytest.LogCaptureFixture,
):
    """Picking the strings extractor is otherwise invisible outside the indexed
    document."""
    strings_result = TikaProcessingResult(
        file_type=PDF_CONTENT_TYPE,
        result=lazybytes_service_inmemory.from_object(TikaResult()),
        handled_by="stringsextractor",
    )

    with caplog.at_level(logging.WARNING):
        chosen = choose_tika_processing_result_task([strings_result])

    assert chosen.handled_by == "stringsextractor"
    assert chosen.result is strings_result.result
    assert "degraded to a last-resort fallback" in caplog.text


def test_chosen_result_carries_the_reasons_the_other_branches_collected(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """Only the winning branch reaches the document, so the reasons move onto it.

    Dropping them leaves a file whose content came from `strings` and whose record of
    why says nothing at all.
    """
    tika_reason = "tika_processor (retries exhausted): TikaTransientError: HTTP 503"
    zip_fallback_result = TikaProcessingResult(
        file_type=PDF_CONTENT_TYPE,
        degradation_reasons=[tika_reason, "zipextractor: BadZipFile: not a zip file"],
    )
    strings_result = TikaProcessingResult(
        file_type=PDF_CONTENT_TYPE,
        result=lazybytes_service_inmemory.from_object(TikaResult()),
        handled_by="stringsextractor",
        degradation_reasons=[tika_reason],
    )

    chosen = choose_tika_processing_result_task([zip_fallback_result, strings_result])

    assert chosen.handled_by == "stringsextractor"
    # Tika's own reason comes back on every branch of the chord, and is listed once.
    assert chosen.degradation_reasons == [
        tika_reason,
        "zipextractor: BadZipFile: not a zip file",
    ]


@pytest.mark.parametrize(
    "file_type, asks_the_model",
    [
        ("image/jpeg", True),
        ("application/pdf", True),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            False,
        ),
        ("text/plain", False),
    ],
)
def test_only_ocr_candidates_reach_the_decision_model(
    ocr_language_agent: MagicMock, file_type: str, asks_the_model: bool
):
    """`X-Tika-OCRLanguage` reaches tesseract for images and PDFs alone, so asking about
    anything else is one inference per file for an answer nothing reads."""
    inferred = infer_language_via_llm_task(
        _bound_task(is_last_attempt=False), file_type, FilePurePath("report")
    )

    assert inferred.file_type == file_type
    assert inferred.language == (TikaCommonOcrLanguage.DEU if asks_the_model else None)
    assert ocr_language_agent.run_sync.called is asks_the_model


def test_other_is_reported_as_no_language(ocr_language_agent: MagicMock):
    """An "other" answer says the name carries no language signal, which is not a
    tesseract language."""
    ocr_language_agent.run_sync.return_value = MagicMock(
        output=TikaCommonOcrLanguage.OTHER
    )

    inferred = infer_language_via_llm_task(
        _bound_task(is_last_attempt=False), "image/jpeg", FilePurePath("report.jpg")
    )

    assert inferred == InferredOcrLanguage("image/jpeg", None)


def test_a_transient_failure_is_raised_while_retries_remain(
    ocr_language_agent: MagicMock,
):
    """An inference service that is restarting is worth asking again before the file is
    indexed with no hint at all."""
    ocr_language_agent.run_sync.side_effect = ModelHTTPError(
        status_code=503, model_name="tev1"
    )

    with pytest.raises(LLMTransientError):
        infer_language_via_llm_task(
            _bound_task(is_last_attempt=False), "image/jpeg", FilePurePath("report.jpg")
        )


def test_a_failed_language_guess_does_not_cost_the_file_its_extraction(
    ocr_language_agent: MagicMock, caplog: pytest.LogCaptureFixture
):
    """This task heads the tika chain, so anything it raises abandons extraction, the
    fallback chord and everything downstream for that file."""
    ocr_language_agent.run_sync.side_effect = ModelHTTPError(
        status_code=404, model_name="typo"
    )

    with caplog.at_level(logging.WARNING):
        inferred = infer_language_via_llm_task(
            _bound_task(is_last_attempt=False), "image/jpeg", FilePurePath("report.jpg")
        )

    assert inferred == InferredOcrLanguage("image/jpeg", None)
    assert "indexing without a language hint" in caplog.text
