from pathlib import Path
from typing import Generator

import pytest
from worker.dependencies import get_rspamd_service
from worker.services.rspamd_service import RspamdService

from utils.consts import ASSETS_DIR

# pylint: disable=redefined-outer-name

EMAIL_ASSETS = [
    ("basic_email.eml", False),
    ("2020-05-05-phishing-email-example-02.eml", True),
]


def bytes_generator(data: bytes) -> Generator[bytes, None, None]:
    yield data


@pytest.fixture()
def rspamd_service() -> RspamdService:
    return get_rspamd_service()


@pytest.mark.parametrize("email_name, is_spam", EMAIL_ASSETS)
def test_detect_spam_from_generator(
    rspamd_service: RspamdService,
    email_name: Path,
    is_spam: bool,
):
    email_asset = ASSETS_DIR / Path(email_name)
    with open(email_asset, "rb") as fd:
        email_bytes = fd.read()
        spam_detected = rspamd_service.detect_spam_from_generator(
            bytes_generator(email_bytes)
        )
        assert spam_detected is is_spam
