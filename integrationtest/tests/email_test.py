import re
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import NamedTuple
from uuid import UUID

import pytest
import requests
from common.dependencies import get_imap_service
from common.services.imap_service import IMAPService

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import get_file_by_name
from utils.upload_asset import upload_asset, upload_bytes_asset

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = [
    "basic_email.eml",
    "unicode_email.eml",
]

A4_HEIGHT_POINTS = 841.89
MEDIABOX_PATTERN = re.compile(rb"/MediaBox\s*\[([^\]]*)\]")


class PdfGeometry(NamedTuple):
    page_count: int
    first_page_height_points: float


def read_pdf_geometry(pdf: bytes) -> PdfGeometry:
    """Read page count and first page height from a PDF's uncompressed page boxes."""
    boxes = MEDIABOX_PATTERN.findall(pdf)
    assert boxes, "no /MediaBox found, this does not look like a PDF"
    bottom, top = (float(value) for value in boxes[0].split()[1::2])
    return PdfGeometry(page_count=len(boxes), first_page_height_points=top - bottom)


def fetch_rendered_file(file_id: UUID, rendered_id: str) -> bytes:
    response = requests.get(
        f"{FILES_ENDPOINT}/{file_id}/rendered/{rendered_id}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


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
        assert indexed_email.rendered_file.browser_pdf_file_id is not None

    subscribed_folders = imap_service.list_subscribed_folders()
    assert (
        len(subscribed_folders) == len(nested_filenames) + 1
    )  # one for api-upload, and the rest for each nested attachment


def test_long_email_renders_as_one_continuous_page():
    """An email has no natural page breaks, so its preview is a single tall page."""
    eml_name = "long_email.eml"
    body = "".join(
        f"<p>Paragraph {index}: the quick brown fox jumps over the lazy dog.</p>"
        for index in range(400)
    )
    msg = MIMEText(f"<html><body>{body}</body></html>", "html", "utf-8")
    msg["Subject"] = "A very long email"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Date"] = formatdate(localtime=True)

    upload_bytes_asset(msg.as_bytes(), upload_file_name=eml_name)

    indexed_email = get_file_by_name(eml_name, wait_for_celery_idle=True)
    rendered_id = indexed_email.rendered_file.browser_pdf_file_id
    assert rendered_id is not None
    # The chromium render is the only preview an email gets: LibreOffice would
    # scale it down to fit its own maximum page size, and an image of it adds
    # nothing the PDF does not already show.
    assert indexed_email.rendered_file.office_pdf_file_id is None
    assert indexed_email.rendered_file.image_file_id is None

    geometry = read_pdf_geometry(
        fetch_rendered_file(indexed_email.file_id, rendered_id)
    )
    assert geometry.page_count == 1
    assert geometry.first_page_height_points > A4_HEIGHT_POINTS
