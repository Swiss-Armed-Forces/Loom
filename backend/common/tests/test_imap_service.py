import hashlib
from pathlib import PurePath
from unittest.mock import MagicMock

import pytest
from imapclient import DELETED, IMAPClient
from imapclient.exceptions import IMAPClientError
from pydantic import AnyUrl

from common.file.file_repository import FilePurePath, ImapPurePath
from common.services.imap_service import (
    IMAP_DEDUPLICATION_HEADER,
    IMAP_DEFAULT_PORT,
    IMAP_DIRECTORY_BASE,
    IMAP_FLAG_NOSELECT,
    ImapFolderInfo,
    IMAPService,
    IMAPServiceError,
    _expunge_all,
    _get_raw_email_with_deduplication_fingerprint,
)

_NON_ASCII_BODY_EMAIL = (
    b"From: sender@example.com\r\n"
    b"To: recipient@example.com\r\n"
    b"Subject: Non-ASCII body\r\n"
    b"Content-Type: text/html\r\n"
    b"Content-Transfer-Encoding: quoted-printable\r\n"
    b"\r\n"
    b"H\xc3\xa4ndler und B\xc3\xb6rsenmakler"
)


class TestIMAPService:
    # pylint: disable=too-many-public-methods

    def test_get_imap_folder_with_none(self):
        result = IMAPService.get_imap_folder(None)
        assert result == IMAP_DIRECTORY_BASE
        assert isinstance(result, ImapPurePath)

    def test_get_imap_folder_with_simple_path(self):
        folder = FilePurePath("Sent")
        result = IMAPService.get_imap_folder(folder)
        assert result == IMAP_DIRECTORY_BASE / "Sent"
        assert isinstance(result, ImapPurePath)

    def test_get_imap_folder_with_nested_path(self):
        folder = FilePurePath("Archive/2024")
        result = IMAPService.get_imap_folder(folder)
        assert result == IMAP_DIRECTORY_BASE / "Archive" / "2024"
        assert isinstance(result, ImapPurePath)

    def test_get_imap_folder_with_absolute_path(self):
        folder = FilePurePath("/Drafts")
        result = IMAPService.get_imap_folder(folder)
        assert result == IMAP_DIRECTORY_BASE / "Drafts"
        assert isinstance(result, ImapPurePath)

    def test_get_imap_folder_with_imap_pure_path(self):
        """Test that ImapPurePath input is returned unchanged."""
        imap_path = ImapPurePath("INBOX/Sent")
        result = IMAPService.get_imap_folder(imap_path)
        assert result is imap_path
        assert isinstance(result, ImapPurePath)

    def test_get_truncated_imap_folder_with_simple_path(self):
        folder = FilePurePath("Archive/2024")
        result = IMAPService.get_truncated_imap_folder(folder, truncation_length=1)
        assert result == IMAP_DIRECTORY_BASE / "A" / "2"
        assert isinstance(result, ImapPurePath)

    def test_get_truncated_imap_folder_with_unicode_path(self):
        folder = FilePurePath("Archive/💩💩💩💩💩💩")
        result = IMAPService.get_truncated_imap_folder(folder, truncation_length=1)
        assert result == IMAP_DIRECTORY_BASE / "A" / "💩"
        assert isinstance(result, ImapPurePath)

    def test_get_truncated_imap_folder_raises_on_invalid(self):
        folder = FilePurePath()
        with pytest.raises(ValueError):
            IMAPService.get_truncated_imap_folder(folder, truncation_length=0)

    def test_get_folder_with_none(self):
        result = IMAPService.get_folder(None)
        assert result is None

    def test_get_folder_with_base_directory(self):
        result = IMAPService.get_folder(IMAP_DIRECTORY_BASE)
        assert result is None

    def test_get_folder_with_simple_path(self):
        imap_folder = ImapPurePath(IMAP_DIRECTORY_BASE / "Sent")
        result = IMAPService.get_folder(imap_folder)
        assert result == FilePurePath("Sent")
        assert isinstance(result, PurePath)
        assert not isinstance(result, ImapPurePath)

    def test_get_folder_with_nested_path(self):
        imap_folder = ImapPurePath(IMAP_DIRECTORY_BASE / "Archive" / "2024")
        result = IMAPService.get_folder(imap_folder)
        assert result == FilePurePath("Archive/2024")
        assert isinstance(result, PurePath)
        assert not isinstance(result, ImapPurePath)

    def test_get_folder_with_pure_path(self):
        """Test that PurePath input is returned unchanged."""
        pure_path = FilePurePath("Sent/2024")
        result = IMAPService.get_folder(pure_path)
        assert result is pure_path
        assert isinstance(result, PurePath)

    def test_roundtrip_conversion_simple(self):
        original = FilePurePath("Sent")
        imap_folder = IMAPService.get_imap_folder(original)
        result = IMAPService.get_folder(imap_folder)
        assert result == original
        assert isinstance(imap_folder, ImapPurePath)
        assert isinstance(result, PurePath)

    def test_roundtrip_conversion_nested(self):
        original = FilePurePath("Archive/2024/January")
        imap_folder = IMAPService.get_imap_folder(original)
        result = IMAPService.get_folder(imap_folder)
        assert result == original
        assert isinstance(imap_folder, ImapPurePath)
        assert isinstance(result, PurePath)

    def test_roundtrip_conversion_none(self):
        imap_folder = IMAPService.get_imap_folder(None)
        result = IMAPService.get_folder(imap_folder)
        assert result is None

    def test_inverse_roundtrip_simple(self):
        original = ImapPurePath(IMAP_DIRECTORY_BASE / "Drafts")
        folder = IMAPService.get_folder(original)
        result = IMAPService.get_imap_folder(folder)
        assert result == original
        assert isinstance(result, ImapPurePath)

    def test_inverse_roundtrip_nested(self):
        original = ImapPurePath(IMAP_DIRECTORY_BASE / "Work" / "Projects" / "2024")
        folder = IMAPService.get_folder(original)
        result = IMAPService.get_imap_folder(folder)
        assert result == original
        assert isinstance(result, ImapPurePath)

    def test_idempotent_get_imap_folder(self):
        folder = FilePurePath("Sent")
        imap_folder1 = IMAPService.get_imap_folder(folder)
        imap_folder2 = IMAPService.get_imap_folder(imap_folder1)
        assert imap_folder1 is imap_folder2

    def test_idempotent_get_folder(self):
        folder = FilePurePath("Sent/2024")
        result = IMAPService.get_folder(folder)
        assert result is folder

    @pytest.mark.parametrize(
        "folder_name",
        [
            "Sent",
            "Drafts",
            "Archive",
            "Trash",
            "Spam",
        ],
    )
    def test_get_imap_folder_common_folders(self, folder_name):
        folder = FilePurePath(folder_name)
        result = IMAPService.get_imap_folder(folder)
        assert result == IMAP_DIRECTORY_BASE / folder_name
        assert isinstance(result, ImapPurePath)

    @pytest.mark.parametrize(
        "path_parts",
        [
            ("Archive", "2024"),
            ("Work", "Projects"),
            ("Personal", "Family", "Photos"),
        ],
    )
    def test_get_imap_folder_nested_folders(self, path_parts):
        folder = FilePurePath(*path_parts)
        result = IMAPService.get_imap_folder(folder)
        expected = IMAP_DIRECTORY_BASE.joinpath(*path_parts)
        assert result == expected
        assert isinstance(result, ImapPurePath)

    def test_get_folder_raises_on_invalid_base(self):
        """Test that get_folder raises ValueError for paths not under
        IMAP_DIRECTORY_BASE."""
        invalid_folder = ImapPurePath("SomeOtherFolder/Subfolder")
        with pytest.raises(ValueError):
            IMAPService.get_folder(invalid_folder)

    def test_get_folder_with_imap_base_returns_none(self):
        """Test that get_folder returns None for IMAP_DIRECTORY_BASE."""
        result = IMAPService.get_folder(ImapPurePath(IMAP_DIRECTORY_BASE))
        assert result is None


class TestGetRawEmailWithDeduplicationFingerprint:
    def test_does_not_raise_on_non_ascii_body(self):
        _get_raw_email_with_deduplication_fingerprint(_NON_ASCII_BODY_EMAIL)

    def test_preserves_body_bytes(self):
        result = _get_raw_email_with_deduplication_fingerprint(_NON_ASCII_BODY_EMAIL)
        assert b"H\xc3\xa4ndler und B\xc3\xb6rsenmakler" in result

    def test_injects_dedup_header(self):
        result = _get_raw_email_with_deduplication_fingerprint(_NON_ASCII_BODY_EMAIL)
        assert f"{IMAP_DEDUPLICATION_HEADER}:".encode() in result

    def test_dedup_header_is_sha256_of_original(self):
        result = _get_raw_email_with_deduplication_fingerprint(_NON_ASCII_BODY_EMAIL)
        expected = hashlib.sha256(_NON_ASCII_BODY_EMAIL).hexdigest().encode()
        assert expected in result

    def test_email_without_body_separator(self):
        headers_only = b"From: sender@example.com\r\nSubject: No body"
        result = _get_raw_email_with_deduplication_fingerprint(headers_only)
        assert f"{IMAP_DEDUPLICATION_HEADER}:".encode() in result


class TestDeleteFolder:
    # pylint: disable=protected-access

    @pytest.fixture(name="client")
    def fixture_client(self) -> MagicMock:
        """Spec'd against IMAPClient so a renamed client method fails loudly."""
        return MagicMock(spec=IMAPClient)

    @pytest.fixture(name="service")
    def fixture_service(self) -> IMAPService:
        return IMAPService(AnyUrl("imap://dovecot.loom:31143"), "user", "pass")

    def test_delete_folder_forwards_to_client(
        self, service: IMAPService, client: MagicMock
    ):
        service._delete_folder(client, "INBOX/Archive")
        client.delete_folder.assert_called_once_with("INBOX/Archive")

    def test_delete_folder_ignores_already_gone_folder(
        self, service: IMAPService, client: MagicMock
    ):
        """Deleting the last child drops the \\Noselect parent along with it."""
        client.delete_folder.side_effect = IMAPClientError(
            "delete failed: [NONEXISTENT] Mailbox doesn't exist: INBOX/Archive"
        )

        service._delete_folder(client, "INBOX/Archive")

        # Assert the call happened: without this the test would also pass if
        # _delete_folder stopped calling delete_folder altogether, never arming
        # the side effect it exists to exercise.
        client.delete_folder.assert_called_once_with("INBOX/Archive")

    def test_delete_folder_raises_on_other_errors(
        self, service: IMAPService, client: MagicMock
    ):
        client.delete_folder.side_effect = IMAPClientError(
            "delete failed: [CANNOT] INBOX can't be deleted"
        )
        with pytest.raises(IMAPServiceError):
            service._delete_folder(client, "INBOX")


class TestExpungeAll:
    def test_flags_whole_mailbox_without_enumerating_uids(self):
        """A sequence set keeps the command O(1) regardless of mailbox size.

        imapclient joins an explicit UID list into one command line, which blows past
        Dovecot's 64 kB imap_max_line_length somewhere around 8k messages.
        """
        client = MagicMock(spec=IMAPClient)

        _expunge_all(client)

        client.add_flags.assert_called_once_with("1:*", [DELETED], silent=True)
        client.expunge.assert_called_once_with()
        client.search.assert_not_called()


class TestImapPort:
    """The port must come from imap_host, not from a literal in the client."""

    def test_uses_port_from_url(self):
        service = IMAPService(AnyUrl("imap://dovecot.loom:31143"), "user", "pass")
        assert service.host.port == 31143

    def test_falls_back_to_protocol_default_without_port(self):
        service = IMAPService(AnyUrl("imap://dovecot.loom"), "user", "pass")
        assert service.host.port is None
        assert IMAP_DEFAULT_PORT == 143


class TestImapFolderInfo:
    def test_is_selectable_without_noselect_flag(self):
        folder = ImapFolderInfo(
            flags=[b"\\HasChildren"],
            delimiter=b"/",
            name=ImapPurePath("INBOX/Test"),
        )
        assert folder.is_selectable is True

    def test_is_selectable_with_noselect_flag(self):
        folder = ImapFolderInfo(
            flags=[IMAP_FLAG_NOSELECT, b"\\HasChildren"],
            delimiter=b"/",
            name=ImapPurePath("INBOX/Test"),
        )
        assert folder.is_selectable is False

    def test_is_selectable_with_empty_flags(self):
        folder = ImapFolderInfo(
            flags=[],
            delimiter=b"/",
            name=ImapPurePath("INBOX/Test"),
        )
        assert folder.is_selectable is True
