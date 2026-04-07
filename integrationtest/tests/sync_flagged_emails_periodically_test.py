from typing import Callable

import pytest
from common.dependencies import get_celery_app, get_imap_service
from common.services.imap_service import IMAPService
from worker.periodic.sync_flagged_emails_periodically_task import (
    sync_flagged_emails_periodically_task,
)

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets

# pylint: disable=redefined-outer-name


def _get_fully_qualified_name(obj: type | Callable):
    module_name = obj.__module__
    qualified_name = obj.__qualname__
    return f"{module_name}.{qualified_name}"


EMAIL_ASSET_LIST = [
    "unicode_email.eml",
    "very_long_email.eml",
    "basic_email.eml",
]

GET_TIMEOUT = 30


@pytest.fixture(autouse=True)
def setup_email_files():
    upload_many_assets(asset_names=EMAIL_ASSET_LIST)

    # Wait for emails to be processed
    search_string = "*"
    file_count = len(EMAIL_ASSET_LIST)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=file_count)


@pytest.fixture()
def imap_service() -> IMAPService:
    return get_imap_service()


def test_sync_flagged_emails_flags_new_emails(imap_service: IMAPService):
    # Flag 2 emails in IMAP
    emails = list(imap_service.get_emails(recurse=True))

    for email in emails[:2]:
        imap_service.add_flags_to_emails(email.folder, [email.uid], [b"\\Flagged"])

    # Run sync task
    fully_qualified_name = _get_fully_qualified_name(
        sync_flagged_emails_periodically_task
    )
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify 2 emails are flagged in Loom
    search_string = 'tika_file_type:"message/rfc822" AND flagged:true'
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)


def test_sync_flagged_emails_mixed_operations(imap_service: IMAPService):
    emails = list(imap_service.get_emails(recurse=True))

    # Flag first 2 emails
    for email in emails[:2]:
        imap_service.add_flags_to_emails(email.folder, [email.uid], [b"\\Flagged"])

    fully_qualified_name = _get_fully_qualified_name(
        sync_flagged_emails_periodically_task
    )
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify 2 flagged
    search_string = "flagged:true"
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)

    imap_service.remove_flags_from_emails(
        emails[0].folder, [emails[0].uid], [b"\\Flagged"]
    )

    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)
    fetch_files_from_api(
        search_string="flagged:false", expected_no_of_files=(len(emails) - 1)
    )

    imap_service.add_flags_to_emails(emails[2].folder, [emails[2].uid], [b"\\Flagged"])
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)
