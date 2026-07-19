import pytest
from common.dependencies import get_imap_service
from common.services.imap_service import IMAPService

from utils.fetch_from_api import get_file_by_name
from utils.upload_asset import upload_asset

# pylint: disable=redefined-outer-name

ASSET_NAME = "basic_email.eml"


@pytest.fixture()
def imap_service() -> IMAPService:
    return get_imap_service()


# Flaky: NOTIFY listener spurious dispatch races with flag-set task.
# https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/work_items/260
@pytest.mark.flaky(reruns=3)
def test_imap_flag_changes_propagate_to_loom(imap_service: IMAPService):
    upload_asset(ASSET_NAME)
    indexed_email = get_file_by_name(ASSET_NAME)
    assert indexed_email.imap is not None

    email = indexed_email.imap

    # Flag the email directly in IMAP — the NOTIFY listener must propagate it to Loom.
    imap_service.add_flags_to_emails(email.folder, [email.uid], [b"\\Flagged"])

    get_file_by_name(ASSET_NAME, search_string="flagged:true")

    # Unflag in IMAP — the NOTIFY listener must clear the flag in Loom.
    imap_service.remove_flags_from_emails(email.folder, [email.uid], [b"\\Flagged"])

    get_file_by_name(ASSET_NAME, search_string="flagged:false")
