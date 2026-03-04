from pathlib import PurePath

import pytest

from common.file.file_repository import FilePurePath, ImapPurePath
from common.services.imap_service import IMAP_DIRECTORY_BASE, IMAPService


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
