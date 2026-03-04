import pytest
from common.dependencies import get_imap_service
from common.services.imap_service import IMAPService

from utils.fetch_from_api import get_file_by_name
from utils.upload_asset import upload_asset

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = [
    "basic_email.eml",
    "unicode_email.eml",
]


@pytest.fixture()
def imap_service() -> IMAPService:
    return get_imap_service()


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSET_NAMES,
)
def test_email_not_seen_after_indexing(imap_service: IMAPService, email: str):
    upload_asset(email)

    indexed_email = get_file_by_name(email)
    assert indexed_email.imap is not None
    indexed_email_full_path = imap_service.get_folder(indexed_email.imap.folder)
    unseen_messages = imap_service.get_emails(
        folder=indexed_email_full_path,
        search_criteria=["UNSEEN"],
    )
    assert len(unseen_messages) == 1
    assert unseen_messages[0] == indexed_email.imap


@pytest.mark.parametrize(
    "email",
    EMAIL_ASSET_NAMES,
)
def test_email_folder_subscribed_after_indexing(imap_service: IMAPService, email: str):
    upload_asset(email)

    indexed_email = get_file_by_name(email)
    assert indexed_email.imap is not None
    subscribed_folders = imap_service.list_subscribed_folders()
    assert len(subscribed_folders) == 1
    assert indexed_email.imap.folder in subscribed_folders
