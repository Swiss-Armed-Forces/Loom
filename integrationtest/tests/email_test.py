from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import pytest
from common.dependencies import get_imap_service
from common.services.imap_service import IMAPService

from utils.fetch_from_api import get_file_by_name
from utils.upload_asset import upload_asset, upload_bytes_asset

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = [
    "basic_email.eml",
    "unicode_email.eml",
]


def create_nested_eml(filenames, depth=0):
    """Recursively create nested EML structure."""
    msg = MIMEMultipart()
    msg["Subject"] = f"Email Level {depth}"
    msg["From"] = f"sender{depth}@example.com"
    msg["To"] = f"recipient{depth}@example.com"
    msg["Date"] = formatdate(localtime=True)

    msg.attach(MIMEText(f"This is email at nesting level {depth}.", "plain", "utf-8"))

    if depth < len(filenames):
        # Create nested email
        nested_content = create_nested_eml(filenames, depth + 1)

        attachment = MIMEBase("message", "rfc822")
        attachment.set_payload(nested_content.as_bytes())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=("utf-8", "", filenames[depth]),
        )
        msg.attach(attachment)

    return msg


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
    unseen_messages = list(
        imap_service.get_emails(
            folder=indexed_email_full_path,
            search_criteria=["UNSEEN"],
        )
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


def test_email_nested_with_long_filename(imap_service: IMAPService):
    nested_filenames = ["💩" * 100 + ".eml", "attachment.eml"]
    eml_name = "has_nested.eml"
    eml = create_nested_eml(nested_filenames)

    upload_bytes_asset(eml.as_bytes(), upload_file_name=eml_name)

    for name in [eml_name] + nested_filenames:
        indexed_email = get_file_by_name(name, wait_for_celery_idle=True)
        assert indexed_email.imap is not None
        # Check if rendered correctly
        assert indexed_email.rendered_file.image_file_id is not None

    subscribed_folders = imap_service.list_subscribed_folders()
    assert (
        len(subscribed_folders) == len(nested_filenames) + 1
    )  # one for api-upload, and the rest for each nested attachment
