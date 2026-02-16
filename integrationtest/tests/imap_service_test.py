from pathlib import Path, PurePath

import pytest
from worker.dependencies import get_imap_service
from worker.services.imap_service import IMAPService

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
]


FOLDER_PATHS = [PurePath(f) for f in FOLDER_NAMES]


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


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_append_same_uuid_as_get_uuid(imap_service: IMAPService, email: bytes):
    info = imap_service.append_email(email)
    uid = imap_service.get_uid_of_email(email)
    assert info.uid == uid


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
    imap_service: IMAPService, email: bytes, folder_path: PurePath
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
    imap_service: IMAPService, email: bytes, folder_path: PurePath
):
    uid = imap_service.get_uid_of_email(email, folder_path)
    assert uid is None


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_not_contain_email_folder_exists(
    imap_service: IMAPService, email: bytes, folder_path: PurePath
):
    imap_service.create_folder(folder_path)

    uid = imap_service.get_uid_of_email(email, folder_path)
    assert uid is None


@pytest.mark.parametrize(
    "email, folder_path",
    [(EMAIL_ASSETS[0], folder_path) for folder_path in FOLDER_PATHS],
)
def test_imap_contains_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: PurePath
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
    parent = PurePath("count_parent")
    child = PurePath("count_parent/child")

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
    root = PurePath("mixed")
    child1 = PurePath("mixed/child1")
    child2 = PurePath("mixed/child2")
    grandchild = PurePath("mixed/child2/grandchild")

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
