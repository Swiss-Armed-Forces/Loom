from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

from common.dependencies import get_file_repository, get_imap_service
from common.file.file_repository import File, FilePurePath, ImapInfo, ImapPurePath

from worker.index_file.tasks.sync_flag_to_imap import (
    IMAP_FLAGGED_FLAG,
    IMAP_SEEN_FLAG,
    sync_imap_flags_task,
)


def _make_file(*, with_imap: bool = True) -> File:
    file = File(
        full_name=FilePurePath("test_email.eml"),
        source="imap",
        sha256="abc123",
        size=42,
    )
    if with_imap:
        file.imap = ImapInfo(uid=1, folder=ImapPurePath("INBOX"))
    return file


class TestSyncImapFlags:
    def test_sets_flagged_flag_in_imap(self):
        file = _make_file()
        assert file.imap is not None
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=True)

        imap_service.add_flags_to_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG],
        )
        imap_service.remove_flags_from_emails.assert_not_called()

    def test_clears_flagged_flag_in_imap(self):
        file = _make_file()
        assert file.imap is not None
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=False)

        imap_service.remove_flags_from_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG],
        )
        imap_service.add_flags_to_emails.assert_not_called()

    def test_sets_both_flags_in_single_call(self):
        file = _make_file()
        assert file.imap is not None
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=True, seen=True)

        imap_service.add_flags_to_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG, IMAP_SEEN_FLAG],
        )
        imap_service.remove_flags_from_emails.assert_not_called()

    def test_clears_both_flags_in_single_call(self):
        file = _make_file()
        assert file.imap is not None
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=False, seen=False)

        imap_service.remove_flags_from_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG, IMAP_SEEN_FLAG],
        )
        imap_service.add_flags_to_emails.assert_not_called()

    def test_adds_flagged_and_removes_seen(self):
        file = _make_file()
        assert file.imap is not None
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=True, seen=False)

        imap_service.add_flags_to_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_FLAGGED_FLAG],
        )
        imap_service.remove_flags_from_emails.assert_called_once_with(
            folder=file.imap.folder,
            uids=[file.imap.uid],
            flags=[IMAP_SEEN_FLAG],
        )

    def test_no_op_when_all_params_are_none(self):
        file = _make_file()
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_)

        imap_service.add_flags_to_emails.assert_not_called()
        imap_service.remove_flags_from_emails.assert_not_called()

    def test_no_op_for_non_imap_file(self):
        file = _make_file(with_imap=False)
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(file.id_, flagged=True, seen=True)

        imap_service.add_flags_to_emails.assert_not_called()
        imap_service.remove_flags_from_emails.assert_not_called()

    def test_no_op_when_file_not_found(self):
        cast(MagicMock, get_file_repository()).get_by_id.return_value = None
        imap_service = cast(MagicMock, get_imap_service())

        sync_imap_flags_task(uuid4(), flagged=True)

        imap_service.add_flags_to_emails.assert_not_called()
        imap_service.remove_flags_from_emails.assert_not_called()
