from datetime import datetime
from pathlib import Path

import pytest
from common.dependencies import get_imap_service
from common.file.file_repository import FilePurePath
from common.services.imap_service import (
    IMAPService,
    IMAPServiceError,
    IMAPServiceErrorFolderNotSelectable,
)

from utils.consts import ASSETS_DIR

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = [
    "basic_email.eml",
    "unicode_email.eml",
    "attachment_pdf.eml",
    "2020-05-05-phishing-email-example-02.eml",
    "attachment_content_disposition.eml",
]

EMAIL_ASSETS = [
    ((ASSETS_DIR / Path(email)).read_bytes()) for email in EMAIL_ASSET_NAMES
]

FOLDER_NAMES = [
    "/absolute",
    "/absolute/subfolder",
    "subfolder",
    "subfolder/subfolder",
    "/Ξξêë💩",
    "Ξξêë💩",
    "Ξξ/êë/💩",
    "very_long_folder_name_" + "x" * 100,
    "very_long_unicode_folder_name_" + "💩" * 20,
]


FOLDER_PATHS = [FilePurePath(f) for f in FOLDER_NAMES]


@pytest.fixture()
def imap_service() -> IMAPService:
    return get_imap_service()


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_append_and_count(imap_service: IMAPService, email: bytes):
    imap_service.append_email(email)

    message_count = imap_service.count_messages()
    assert message_count == 1


@pytest.mark.parametrize("recurse", (True, False))
def test_imap_count_messages_returns_0_on_non_existing_folder(
    imap_service: IMAPService, recurse: bool
):
    count = imap_service.count_messages(
        FilePurePath("this/folder/does/not/exist"), recurse=recurse
    )
    assert count == 0


@pytest.mark.parametrize("recurse", (True, False))
def test_imap_get_emails_raises_on_non_existing_folder(
    imap_service: IMAPService, recurse: bool
):
    with pytest.raises(IMAPServiceError):
        imap_service.get_emails(
            folder=FilePurePath("this/folder/does/not/exist"), recurse=recurse
        )


def test_imap_add_flags_to_emails_raises_on_non_existing_folder(
    imap_service: IMAPService,
):
    with pytest.raises(IMAPServiceErrorFolderNotSelectable):
        imap_service.add_flags_to_emails(
            folder=FilePurePath("this/folder/does/not/exist"),
            uids=[],
            flags=[],
        )


def test_imap_remove_flags_from_emails_raises_on_non_existing_folder(
    imap_service: IMAPService,
):
    with pytest.raises(IMAPServiceErrorFolderNotSelectable):
        imap_service.remove_flags_from_emails(
            folder=FilePurePath("this/folder/does/not/exist"),
            uids=[],
            flags=[],
        )


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_append_same_uuid_as_get_uuid(imap_service: IMAPService, email: bytes):
    info = imap_service.append_email(email)
    uid = imap_service.get_uid_of_email(email)
    assert info.uid == uid


def test_imap_get_uid_of_email_non_existing_folder(imap_service: IMAPService):
    uid = imap_service.get_uid_of_email(
        EMAIL_ASSETS[0], FilePurePath("this/folder/does/not/exist")
    )
    assert uid is None


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_get_uuid_no_match(imap_service: IMAPService, email: bytes):
    uid = imap_service.get_uid_of_email(email)
    assert uid is None


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_append_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: FilePurePath
):
    imap_service.append_email(email, folder_path)

    message_count = imap_service.count_messages()
    assert message_count == 0

    message_count_subfolder = imap_service.count_messages(folder_path)
    assert message_count_subfolder == 1


@pytest.mark.parametrize(
    "email",
    (EMAIL_ASSETS[0],),
)
def test_imap_double_append_email(imap_service: IMAPService, email: bytes):
    imap_service.append_email(email)
    imap_service.append_email(email)

    message_count = imap_service.count_messages()
    assert message_count == 2


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_not_contain_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: FilePurePath
):
    uid = imap_service.get_uid_of_email(email, folder_path)
    assert uid is None


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_not_contain_email_folder_exists(
    imap_service: IMAPService, email: bytes, folder_path: FilePurePath
):
    imap_service.create_folder(folder_path)

    uid = imap_service.get_uid_of_email(email, folder_path)
    assert uid is None


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_contains_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: FilePurePath
):
    imap_service.append_email(email, folder_path)

    uid = imap_service.get_uid_of_email(email, folder_path)
    assert uid is not None


def test_imap_count_messages_recurse_no_messages(imap_service: IMAPService):
    # No messages anywhere
    assert imap_service.count_messages(recurse=True) == 0


def test_imap_count_messages_recurse_inbox_only(imap_service: IMAPService):
    # Only messages in INBOX
    imap_service.append_email(EMAIL_ASSETS[0])
    imap_service.append_email(EMAIL_ASSETS[1])
    imap_service.append_email(EMAIL_ASSETS[2])

    assert imap_service.count_messages() == 3
    assert imap_service.count_messages(recurse=True) == 3


def test_imap_count_messages_recurse_subfolders_only(imap_service: IMAPService):
    # Messages only in subfolders, INBOX empty
    parent = FilePurePath("count_parent")
    child = FilePurePath("count_parent/child")

    imap_service.append_email(EMAIL_ASSETS[0], parent)
    imap_service.append_email(EMAIL_ASSETS[1], child)
    imap_service.append_email(EMAIL_ASSETS[2], child)

    # INBOX has none directly
    assert imap_service.count_messages() == 0

    # Subtree counts
    assert imap_service.count_messages(parent) == 1
    assert imap_service.count_messages(child) == 2
    assert imap_service.count_messages(parent, recurse=True) == 3

    # Whole account under INBOX should see them too
    assert imap_service.count_messages(recurse=True) == 3


def test_imap_count_messages_recurse_mixed_depth(imap_service: IMAPService):
    root = FilePurePath("mixed")
    child1 = FilePurePath("mixed/child1")
    child2 = FilePurePath("mixed/child2")
    grandchild = FilePurePath("mixed/child2/grandchild")

    imap_service.append_email(EMAIL_ASSETS[0], root)  # 1 in root
    imap_service.append_email(EMAIL_ASSETS[1], child1)  # 1 in child1
    imap_service.append_email(EMAIL_ASSETS[2], child2)  # 1 in child2
    imap_service.append_email(EMAIL_ASSETS[3], grandchild)  # 1 in grandchild

    assert imap_service.count_messages(root) == 1
    assert imap_service.count_messages(child1) == 1
    assert imap_service.count_messages(child2) == 1
    assert imap_service.count_messages(grandchild) == 1

    # Recursive counts
    assert imap_service.count_messages(root, recurse=True) == 4
    assert imap_service.count_messages(child2, recurse=True) == 2


def test_imap_create_folder_name_too_long(imap_service: IMAPService):
    too_long = FilePurePath("💩" * 100)
    with pytest.raises(IMAPServiceError, match="too long"):
        imap_service.create_folder(too_long)


def test_imap_append_name_too_long(imap_service: IMAPService):
    too_long = FilePurePath("💩" * 100)
    with pytest.raises(IMAPServiceError, match="too long"):
        imap_service.append_email(EMAIL_ASSETS[0], too_long)


@pytest.mark.parametrize(
    "folder_structure,get_emails_args,expected_matches",
    [
        (
            {
                FilePurePath("email_test"): [None, None, None],
                FilePurePath("email_test/subfolder"): [None],
                FilePurePath("email_test/subfolder/deep"): [None, None],
            },
            (
                None,
                FilePurePath("email_test"),
                False,
            ),
            3,
        ),
        (
            {
                FilePurePath("email_test"): [None, None, None],
                FilePurePath("email_test/subfolder"): [None],
                FilePurePath("email_test/subfolder/deep"): [None, None],
            },
            (
                None,
                FilePurePath("email_test"),
                True,
            ),
            6,
        ),
        # Get SEEN emails only (recursive)
        (
            {
                FilePurePath("email_test"): [None, [b"\\Seen"], None],
                FilePurePath("email_test/subfolder"): [None],
                FilePurePath("email_test/subfolder/deep"): [[b"\\Seen"], None],
            },
            (
                ["SEEN"],
                None,
                True,
            ),
            2,
        ),
        # Get FLAGGED emails only (recursive)
        (
            {
                FilePurePath("email_test"): [None, [b"\\Flagged"], [b"\\Flagged"]],
                FilePurePath("email_test/subfolder"): [[b"\\Flagged"]],
            },
            (
                ["FLAGGED"],
                None,
                True,
            ),
            3,
        ),
        # Combined criteria - FLAGGED and SEEN
        (
            {
                FilePurePath("email_test"): [None, [b"\\Seen", b"\\Flagged"], None],
                FilePurePath("email_test/subfolder"): [None],
                FilePurePath("email_test/subfolder/deep"): [[b"\\Seen"], None],
            },
            (
                ["FLAGGED", "SEEN"],
                FilePurePath("email_test"),
                True,
            ),
            1,
        ),
    ],
)
def test_imap_get_emails(
    imap_service: IMAPService,
    folder_structure: dict[FilePurePath, list[list[bytes] | None]],
    get_emails_args: tuple[list[str] | None, FilePurePath | None, bool],
    expected_matches: int,
):

    for folder_path, emails in folder_structure.items():
        for flags in emails:
            info = imap_service.append_email(EMAIL_ASSETS[0], folder_path)
            if flags is None:
                continue
            imap_service.add_flags_to_emails(info.folder, [info.uid], flags)

    # Search for emails
    results = imap_service.get_emails(*get_emails_args)

    # Verify count
    assert len(results) == expected_matches


def test_get_latest_email_date_empty_folder(imap_service: IMAPService):
    result = imap_service.get_latest_email_date()
    assert result is None


def test_get_latest_email_date(imap_service: IMAPService):
    imap_service.append_email(EMAIL_ASSETS[0])

    result = imap_service.get_latest_email_date()
    assert result is not None
    assert isinstance(result, datetime)


def test_unsubscribe_folder(imap_service: IMAPService):
    folder = FilePurePath("unsubscribe_test")
    imap_folder = imap_service.get_imap_folder(folder)

    imap_service.create_folder(imap_folder)

    # Subscribe to folder
    imap_service.subscribe_folder(imap_folder)
    subscribed = imap_service.list_subscribed_folders()
    assert imap_folder in subscribed

    # Unsubscribe from folder
    imap_service.unsubscribe_folder(folder)
    subscribed = imap_service.list_subscribed_folders()
    assert imap_folder not in subscribed


def test_subscribe_unsubscribe_folder_recurse(imap_service: IMAPService):
    parent = FilePurePath("subscribe_unsubscribe_recurse_test")
    child = FilePurePath("subscribe_unsubscribe_recurse_test/child")
    grandchild = FilePurePath("subscribe_unsubscribe_recurse_test/child/grandchild")

    parent_imap = imap_service.get_imap_folder(parent)
    child_imap = imap_service.get_imap_folder(child)
    grandchild_imap = imap_service.get_imap_folder(grandchild)

    # Create folder hierarchy
    imap_service.create_folder(parent_imap)
    imap_service.create_folder(child_imap)
    imap_service.create_folder(grandchild_imap)

    # Subscribe recursively from parent
    imap_service.subscribe_folder(parent, recurse=True)

    # Verify all folders are subscribed
    subscribed = imap_service.list_subscribed_folders()
    assert parent_imap in subscribed
    assert child_imap in subscribed
    assert grandchild_imap in subscribed

    # Unsubscribe recursively from parent
    imap_service.unsubscribe_folder(parent, recurse=True)

    # Verify all folders are unsubscribed
    subscribed = imap_service.list_subscribed_folders()
    assert parent_imap not in subscribed
    assert child_imap not in subscribed
    assert grandchild_imap not in subscribed


def test_imap_subscribe_folder_raises_on_non_existing_folder(imap_service: IMAPService):
    invalid_folder = FilePurePath("this/folder/does/not/exist")
    with pytest.raises(IMAPServiceError):
        imap_service.subscribe_folder(invalid_folder)


def test_imap_unsubscribe_folder_raises_on_folder_with_invalid_name(
    imap_service: IMAPService,
):
    invalid_folder = FilePurePath("invalid\x00name")
    with pytest.raises(IMAPServiceError):
        imap_service.unsubscribe_folder(invalid_folder)


def test_subscribe_folder_recurse_only_subscribes_selectable_folders(
    imap_service: IMAPService,
):
    """Test that recursive subscription works and only subscribes to selectable folders.

    Note: Creating true NOSELECT folders is server-dependent. This test verifies
    the existing recursive subscription behavior continues to work correctly.
    The NOSELECT filtering is verified by unit tests.
    """
    parent = FilePurePath("subscribe_selectable_test")
    child = FilePurePath("subscribe_selectable_test/child")
    grandchild = FilePurePath("subscribe_selectable_test/child/grandchild")

    parent_imap = imap_service.get_imap_folder(parent)
    child_imap = imap_service.get_imap_folder(child)
    grandchild_imap = imap_service.get_imap_folder(grandchild)

    # Create folder hierarchy
    imap_service.create_folder(parent_imap)
    imap_service.create_folder(child_imap)
    imap_service.create_folder(grandchild_imap)

    # Subscribe recursively from parent
    imap_service.subscribe_folder(parent, recurse=True)

    # Verify all selectable folders are subscribed
    subscribed = imap_service.list_subscribed_folders()
    assert parent_imap in subscribed
    assert child_imap in subscribed
    assert grandchild_imap in subscribed

    # Cleanup
    imap_service.unsubscribe_folder(parent, recurse=True)
