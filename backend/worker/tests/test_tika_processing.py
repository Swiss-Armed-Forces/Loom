import logging
from typing import cast
from unittest.mock import MagicMock

import pytest
from common.file.file_repository import File, FilePurePath
from common.services.lazybytes_service import InMemoryTempLazyBytesService

from worker.dependencies import get_tika_service
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.tika_processing import (
    TIKA_RETRY_EXCEPTIONS,
    TikaProcessingResult,
    choose_tika_processing_result_task,
    tika_processor_task,
)
from worker.services.tika_service import (
    TikaPermanentError,
    TikaResult,
    TikaTransientError,
)

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


def test_parsed_document_is_handled_by_tika(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    tika_service.parse_from_generator.return_value = TikaResult()
    content = lazybytes_service_inmemory.from_bytes(data=b"%PDF-1.7")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False), PDF_CONTENT_TYPE, content, _file()
    )

    assert result.handled_by == "tika_processor"
    assert result.result is not None
    assert not result.exceptions


def test_forced_fallback_content_type_never_reaches_tika(
    tika_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """These types have dedicated extractors, so tika is skipped rather than failed."""
    content = lazybytes_service_inmemory.from_bytes(data=b"anything")

    result = tika_processor_task(
        _bound_task(is_last_attempt=False),
        FORCED_FALLBACK_CONTENT_TYPE,
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
            _bound_task(is_last_attempt=False), PDF_CONTENT_TYPE, content, _file()
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
            _bound_task(is_last_attempt=True), PDF_CONTENT_TYPE, content, _file()
        )

    assert result.result is None
    assert result.handled_by is None
    assert len(result.exceptions) == 1
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
        _bound_task(is_last_attempt=False), PDF_CONTENT_TYPE, content, _file()
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
        _bound_task(is_last_attempt=False), PDF_CONTENT_TYPE, content, _file()
    )

    assert result.result is None
    assert len(result.exceptions) == 1


def test_only_transient_failures_are_declared_retryable():
    """The invariant the retry classification rests on, and one a refactor breaks
    quietly."""
    assert TikaTransientError in TIKA_RETRY_EXCEPTIONS
    assert TikaPermanentError not in TIKA_RETRY_EXCEPTIONS


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

    assert chosen is strings_result
    assert "degraded to a last-resort fallback" in caplog.text
