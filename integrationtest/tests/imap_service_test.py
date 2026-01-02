from pathlib import Path, PurePath

import pytest
from worker.dependencies import get_imap_service
from worker.services.imap_service import IMAPService

from utils.consts import ASSETS_DIR

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = ["basic_email.eml", "attachment_pdf.eml"]

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
def test_imap_append_email(imap_service: IMAPService, email: bytes):
    imap_service.append_email(email)

    message_count = imap_service.count_messages()
    assert message_count == 1


@pytest.mark.parametrize(
    "email, folder_path",
    [(email, folder_path) for email in EMAIL_ASSETS for folder_path in FOLDER_PATHS],
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
    EMAIL_ASSETS,
)
def test_imap_double_append_email(imap_service: IMAPService, email: bytes):
    imap_service.append_email(email)
    imap_service.append_email(email)

    message_count = imap_service.count_messages()
    assert message_count == 2


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_not_contain_email(imap_service: IMAPService, email: bytes):
    duplicate_found = imap_service.contains_email(email)
    assert duplicate_found is False


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSETS,
)
def test_imap_contains_email(imap_service: IMAPService, email: bytes):
    imap_service.append_email(email)

    duplicate_found = imap_service.contains_email(email)
    assert duplicate_found is True


@pytest.mark.parametrize(
    "email, folder_path",
    [(email, folder_path) for email in EMAIL_ASSETS for folder_path in FOLDER_PATHS],
)
def test_imap_not_contain_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: PurePath
):
    duplicate_found = imap_service.contains_email(email, folder_path)
    assert duplicate_found is False


@pytest.mark.parametrize(
    "email, folder_path",
    [(email, folder_path) for email in EMAIL_ASSETS for folder_path in FOLDER_PATHS],
)
def test_imap_not_contain_email_folder_exists(
    imap_service: IMAPService, email: bytes, folder_path: PurePath
):
    imap_service.create_folder(folder_path)

    duplicate_found = imap_service.contains_email(email, folder_path)
    assert duplicate_found is False


@pytest.mark.parametrize(
    "email, folder_path",
    [(email, folder_path) for email in EMAIL_ASSETS for folder_path in FOLDER_PATHS],
)
def test_imap_contains_email_folder(
    imap_service: IMAPService, email: bytes, folder_path: PurePath
):
    imap_service.append_email(email, folder_path)

    duplicate_found = imap_service.contains_email(email, folder_path)
    assert duplicate_found is True
