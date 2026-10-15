from typing import cast
from unittest.mock import MagicMock

import pytest
from common.services.lazybytes_service import InMemoryTempLazyBytesService

from worker.dependencies import get_rspamd_service
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.email_processing import (
    RSPAMD_RETRY_EXCEPTIONS,
    detect_spam_task,
)
from worker.services.rspamd_service import RspamdPermanentError, RspamdTransientError

# pylint: disable=redefined-outer-name


def _bound_task(*, is_last_attempt: bool) -> FileIndexingTask:
    task = MagicMock(spec=FileIndexingTask)
    task.is_last_attempt = is_last_attempt
    return cast(FileIndexingTask, task)


@pytest.fixture()
def rspamd_service() -> MagicMock:
    return cast(MagicMock, get_rspamd_service())


def test_transient_failure_is_raised_while_retries_remain(
    rspamd_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    rspamd_service.detect_spam_from_generator.side_effect = RspamdTransientError(
        "HTTP 503"
    )
    content = lazybytes_service_inmemory.from_bytes(data=b"From: a@b\n\nhi")

    with pytest.raises(RspamdTransientError):
        detect_spam_task(_bound_task(is_last_attempt=False), True, content)


@pytest.mark.parametrize(
    "error",
    [RspamdTransientError("HTTP 503"), RspamdPermanentError("HTTP 415")],
)
def test_unscannable_email_is_indexed_as_not_spam(
    error: Exception,
    rspamd_service: MagicMock,
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """Failing here would take the body, attachments and rendering down with it.

    The permanent case degrades immediately; the transient one only once its budget is
    spent, which is why both are driven with is_last_attempt set.
    """
    rspamd_service.detect_spam_from_generator.side_effect = error
    content = lazybytes_service_inmemory.from_bytes(data=b"From: a@b\n\nhi")

    assert detect_spam_task(_bound_task(is_last_attempt=True), True, content) is False


def test_non_email_is_never_scanned(rspamd_service: MagicMock):
    assert detect_spam_task(_bound_task(is_last_attempt=False), False, None) is False
    rspamd_service.detect_spam_from_generator.assert_not_called()


def test_only_transient_failures_are_declared_retryable():
    assert RspamdTransientError in RSPAMD_RETRY_EXCEPTIONS
    assert RspamdPermanentError not in RSPAMD_RETRY_EXCEPTIONS
