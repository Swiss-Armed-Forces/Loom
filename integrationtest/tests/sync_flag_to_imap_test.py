import pytest
import requests
from common.dependencies import get_imap_service
from common.services.imap_service import IMAPService
from common.services.task_scheduling_service import UpdateFileRequest

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api, get_file_by_name
from utils.upload_asset import upload_asset

# pylint: disable=redefined-outer-name

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

ASSET_NAME = "basic_email.eml"


@pytest.fixture()
def imap_service() -> IMAPService:
    return get_imap_service()


def _update_file(file_id, update: UpdateFileRequest):
    response = requests.put(
        f"{FILES_ENDPOINT}/{file_id}",
        json=update.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def test_flagging_email_in_loom_sets_flag_in_imap(imap_service: IMAPService):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    # Confirm no IMAP flags initially
    assert not list(imap_service.get_emails(["FLAGGED"], recurse=True))

    # Flag via Loom API
    _update_file(indexed_email.file_id, UpdateFileRequest(flagged=True))

    # update_file and sync_flag_to_imap run as a parallel Celery group, so the
    # ES search result only confirms update_file has finished. wait_for_celery_idle
    # ensures sync_flag_to_imap has also completed before we check the IMAP state.
    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND flagged:true',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # The \Flagged flag must now be set in IMAP
    flagged_in_imap = list(imap_service.get_emails(["FLAGGED"], recurse=True))
    assert len(flagged_in_imap) == 1
    assert flagged_in_imap[0] == indexed_email.imap


def test_unflagging_email_in_loom_clears_flag_in_imap(imap_service: IMAPService):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    # Pre-set the flag directly in IMAP
    imap_service.add_flags_to_emails(
        folder=indexed_email.imap.folder,
        uids=[indexed_email.imap.uid],
        flags=[b"\\Flagged"],
    )
    assert len(list(imap_service.get_emails(["FLAGGED"], recurse=True))) == 1

    # Wait for the NOTIFY listener to propagate \Flagged to ES before calling the
    # Loom API. Without this, the NOTIFY-triggered update_task(flagged=True) can
    # race with our update_task(flagged=False) and overwrite it.
    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND flagged:true',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # Unflag via Loom API
    _update_file(indexed_email.file_id, UpdateFileRequest(flagged=False))

    # update_file and sync_flag_to_imap run as a parallel Celery group, so the
    # ES search result only confirms update_file has finished. wait_for_celery_idle
    # ensures sync_flag_to_imap has also completed before we check the IMAP state.
    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND flagged:false',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # The \Flagged flag must now be cleared in IMAP
    assert not list(imap_service.get_emails(["FLAGGED"], recurse=True))


def test_marking_email_seen_in_loom_sets_seen_in_imap(imap_service: IMAPService):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    # Confirm no \Seen flag initially
    assert not list(imap_service.get_emails(["SEEN"], recurse=True))

    # Mark as seen via Loom API
    _update_file(indexed_email.file_id, UpdateFileRequest(seen=True))

    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND seen:true',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # The \Seen flag must now be set in IMAP
    seen_in_imap = list(imap_service.get_emails(["SEEN"], recurse=True))
    assert len(seen_in_imap) == 1
    assert seen_in_imap[0] == indexed_email.imap


def test_marking_email_unseen_in_loom_clears_seen_in_imap(imap_service: IMAPService):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    # Pre-set \Seen directly in IMAP
    imap_service.add_flags_to_emails(
        folder=indexed_email.imap.folder,
        uids=[indexed_email.imap.uid],
        flags=[b"\\Seen"],
    )
    assert len(list(imap_service.get_emails(["SEEN"], recurse=True))) == 1

    # Wait for the NOTIFY listener to propagate \Seen to ES before calling the
    # Loom API. Without this, the NOTIFY-triggered update_task(seen=True) can
    # race with our update_task(seen=False) and overwrite it.
    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND seen:true',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # Mark as unseen via Loom API
    _update_file(indexed_email.file_id, UpdateFileRequest(seen=False))

    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND seen:false',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # The \Seen flag must now be cleared in IMAP
    assert not list(imap_service.get_emails(["SEEN"], recurse=True))


def test_flagging_and_seeing_simultaneously_sets_both_in_imap(
    imap_service: IMAPService,
):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    # Confirm no flags initially
    assert not list(imap_service.get_emails(["FLAGGED"], recurse=True))
    assert not list(imap_service.get_emails(["SEEN"], recurse=True))

    # Set both flags simultaneously via Loom API
    _update_file(indexed_email.file_id, UpdateFileRequest(flagged=True, seen=True))

    fetch_files_from_api(
        search_string=f'short_name:"{ASSET_NAME}" AND flagged:true AND seen:true',
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    # Both \Flagged and \Seen must be set in IMAP
    flagged_in_imap = list(imap_service.get_emails(["FLAGGED"], recurse=True))
    seen_in_imap = list(imap_service.get_emails(["SEEN"], recurse=True))
    assert len(flagged_in_imap) == 1
    assert flagged_in_imap[0] == indexed_email.imap
    assert len(seen_in_imap) == 1
    assert seen_in_imap[0] == indexed_email.imap
