# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock

import pytest
from common.file.file_repository import FileNotFoundException
from common.services.task_scheduling_service import UpdateFileRequest

from crawler.imap_notify_listener_service import IMAPNotifyListenerService


@pytest.fixture
def file_repository():
    return MagicMock()


@pytest.fixture
def file_scheduling_service():
    return MagicMock()


@pytest.fixture
def make_service(file_repository, file_scheduling_service):
    def _make() -> IMAPNotifyListenerService:
        return IMAPNotifyListenerService(
            host="localhost",
            port=143,
            user="user",
            password="pass",
            file_repository=file_repository,
            file_scheduling_service=file_scheduling_service,
        )

    return _make


class TestParseStatusFolder:
    def test_bytes_mailbox_decoded(self):
        response = (b"STATUS", b"INBOX/Work", (b"HIGHESTMODSEQ", 47))
        assert IMAPNotifyListenerService.parse_status_folder(response) == "INBOX/Work"

    def test_string_mailbox_returned(self):
        response = (b"STATUS", "INBOX/Work", (b"HIGHESTMODSEQ", 47))
        assert IMAPNotifyListenerService.parse_status_folder(response) == "INBOX/Work"

    def test_fetch_response_returns_none(self):
        response = (1, b"FETCH", (b"UID", 10, b"FLAGS", ()))
        assert IMAPNotifyListenerService.parse_status_folder(response) is None

    def test_exists_response_returns_none(self):
        assert IMAPNotifyListenerService.parse_status_folder((3, b"EXISTS")) is None

    def test_short_response_returns_none(self):
        assert IMAPNotifyListenerService.parse_status_folder((b"STATUS",)) is None

    def test_empty_response_returns_none(self):
        assert IMAPNotifyListenerService.parse_status_folder(()) is None


class TestHandleFetchResponse:
    def test_well_formed_fetch_schedules_update(
        self, make_service, file_repository, file_scheduling_service
    ):
        file = MagicMock()
        file.id_ = "abc-123"
        file_repository.get_email_from_imap_info.return_value = file

        service = make_service()
        # imapclient returns a flat tuple: (seq, b'FETCH', (key, val, key, val, ...))
        response = (
            7,
            b"FETCH",
            (b"UID", 1023, b"MAILBOX", b"INBOX", b"FLAGS", (b"\\Seen",)),
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_called_once_with(
            "abc-123",
            UpdateFileRequest(flagged=False, seen=True),
        )

    def test_flagged_and_seen_flags(
        self, make_service, file_repository, file_scheduling_service
    ):
        file = MagicMock()
        file.id_ = "xyz"
        file_repository.get_email_from_imap_info.return_value = file

        service = make_service()
        response = (
            3,
            b"FETCH",
            (
                b"UID",
                42,
                b"MAILBOX",
                b"INBOX/Work",
                b"FLAGS",
                (b"\\Seen", b"\\Flagged"),
            ),
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_called_once_with(
            "xyz",
            UpdateFileRequest(flagged=True, seen=True),
        )

    def test_missing_flags_ignored(self, make_service, file_scheduling_service):
        service = make_service()
        response = (
            1,
            b"FETCH",
            (b"UID", 10, b"MAILBOX", b"INBOX"),
            # no FLAGS item
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_not_called()

    def test_missing_mailbox_ignored(self, make_service, file_scheduling_service):
        service = make_service()
        response = (
            1,
            b"FETCH",
            (b"UID", 10, b"FLAGS", (b"\\Seen",)),
            # no MAILBOX item
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_not_called()

    def test_expunge_response_ignored(self, make_service, file_scheduling_service):
        service = make_service()
        service.handle_fetch_response((5, b"EXPUNGE", ()))

        file_scheduling_service.update_file.assert_not_called()

    def test_non_fetch_response_ignored(self, make_service, file_scheduling_service):
        service = make_service()
        service.handle_fetch_response((1, b"EXISTS", 10))

        file_scheduling_service.update_file.assert_not_called()

    def test_malformed_response_no_crash(self, make_service, file_scheduling_service):
        service = make_service()
        service.handle_fetch_response((1, b"FETCH", "not-a-tuple"))
        service.handle_fetch_response((1,))

        file_scheduling_service.update_file.assert_not_called()

    def test_mailbox_string_value_decoded(
        self, make_service, file_repository, file_scheduling_service
    ):
        file = MagicMock()
        file.id_ = "sent-1"
        file_repository.get_email_from_imap_info.return_value = file

        service = make_service()
        response = (
            2,
            b"FETCH",
            (
                b"UID",
                99,
                b"MAILBOX",
                "Sent",  # string, not bytes
                b"FLAGS",
                (b"\\Seen",),
            ),
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_called_once_with(
            "sent-1",
            UpdateFileRequest(flagged=False, seen=True),
        )

    def test_empty_flags_schedules_update_with_both_false(
        self, make_service, file_repository, file_scheduling_service
    ):
        file = MagicMock()
        file.id_ = "f1"
        file_repository.get_email_from_imap_info.return_value = file

        service = make_service()
        response = (
            4,
            b"FETCH",
            (b"UID", 5, b"MAILBOX", b"INBOX", b"FLAGS", ()),
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_called_once_with(
            "f1",
            UpdateFileRequest(flagged=False, seen=False),
        )

    def test_file_not_found_skips_update(
        self, make_service, file_repository, file_scheduling_service
    ):
        file_repository.get_email_from_imap_info.side_effect = FileNotFoundException(
            "not found"
        )

        service = make_service()
        response = (
            1,
            b"FETCH",
            (b"UID", 7, b"MAILBOX", b"INBOX", b"FLAGS", (b"\\Seen",)),
        )
        service.handle_fetch_response(response)

        file_scheduling_service.update_file.assert_not_called()
