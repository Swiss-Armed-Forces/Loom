from pathlib import Path

import pytest
from worker.index_file.processor.email_processor import (
    detect_spam,
    upload_email_to_imap,
)

from utils.consts import ASSETS_DIR


@pytest.mark.parametrize(
    "asset,is_spam",
    [
        ("basic_email.eml", False),
        ("2020-05-05-phishing-email-example-02.eml", True),
    ],
)
def test_detect_spam(asset: str, is_spam: bool):
    email = ASSETS_DIR / asset
    with open(email, "rb") as fd:
        data = memoryview(fd.read())

    spam_detected = detect_spam(data)

    assert spam_detected is is_spam


@pytest.mark.parametrize(
    "asset",
    [
        "basic_email.eml",
    ],
)
def test_upload_email_to_imap(asset: str):
    email = ASSETS_DIR / asset
    with open(email, "rb") as fd:
        data = memoryview(fd.read())

    upload_email_to_imap(Path(asset), data)
