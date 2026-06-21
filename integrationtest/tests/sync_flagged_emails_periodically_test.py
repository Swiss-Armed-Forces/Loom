from typing import Callable

import pytest
from common.dependencies import get_celery_app, get_imap_service
from common.services.imap_service import IMAPService
from worker.periodic.sync_imap_flags_periodically_task import (
    sync_imap_flags_periodically_task,
)

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets

# pylint: disable=redefined-outer-name

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")


def _get_fully_qualified_name(obj: type | Callable):
    module_name = obj.__module__
    qualified_name = obj.__qualname__
    return f"{module_name}.{qualified_name}"


EMAIL_ASSET_LIST = [
    "unicode_email.eml",
    "2020-05-05-phishing-email-example-02.eml",
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
    fully_qualified_name = _get_fully_qualified_name(sync_imap_flags_periodically_task)
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify 2 emails are flagged in Loom
    search_string = 'tika_file_type:"message/rfc822" AND flagged:true'
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)


def test_sync_flagged_emails_preserves_loom_flags_when_imap_flag_removed(
    imap_service: IMAPService,
):
    emails = list(imap_service.get_emails(recurse=True))

    # Flag first 2 emails in IMAP
    for email in emails[:2]:
        imap_service.add_flags_to_emails(email.folder, [email.uid], [b"\\Flagged"])

    fully_qualified_name = _get_fully_qualified_name(sync_imap_flags_periodically_task)
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify 2 flagged in Loom
    search_string = "flagged:true"
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)

    # Remove IMAP flag from first email — Loom flag must be preserved
    imap_service.remove_flags_from_emails(
        emails[0].folder, [emails[0].uid], [b"\\Flagged"]
    )

    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)

    # Flag a third email in IMAP — sync picks it up, total becomes 3
    imap_service.add_flags_to_emails(emails[2].folder, [emails[2].uid], [b"\\Flagged"])
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=3)


def test_sync_seen_emails_marks_new_emails_seen(imap_service: IMAPService):
    # Mark 2 emails as seen in IMAP
    emails = list(imap_service.get_emails(recurse=True))

    for email in emails[:2]:
        imap_service.add_flags_to_emails(email.folder, [email.uid], [b"\\Seen"])

    # Run sync task
    fully_qualified_name = _get_fully_qualified_name(sync_imap_flags_periodically_task)
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify 2 emails are marked seen in Loom
    search_string = 'tika_file_type:"message/rfc822" AND seen:true'
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)


def test_sync_email_both_flagged_and_seen_updates_both_in_loom(
    imap_service: IMAPService,
):
    emails = list(imap_service.get_emails(recurse=True))

    # Mark first email as both FLAGGED and SEEN in IMAP
    imap_service.add_flags_to_emails(
        emails[0].folder, [emails[0].uid], [b"\\Flagged", b"\\Seen"]
    )

    fully_qualified_name = _get_fully_qualified_name(sync_imap_flags_periodically_task)
    get_celery_app().send_task(fully_qualified_name).get(timeout=GET_TIMEOUT)

    # Verify the email is both flagged and seen in Loom
    fetch_files_from_api(
        search_string="flagged:true AND seen:true", expected_no_of_files=1
    )
    # Verify only one email was processed (no duplicate pipelines)
    fetch_files_from_api(search_string="flagged:true", expected_no_of_files=1)
    fetch_files_from_api(search_string="seen:true", expected_no_of_files=1)
