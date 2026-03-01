from pathlib import Path
from typing import Generator

import pytest
from worker.dependencies import get_rspamd_service
from worker.services.rspamd_service import RspamdService

from utils.consts import ASSETS_DIR

# pylint: disable=redefined-outer-name

EMAIL_ASSET_NAMES = [
    ("basic_email.eml", False),
    ("2020-05-05-phishing-email-example-02.eml", True),
]

EMAIL_ASSETS = [
    (
        Path(email[0]),
        (ASSETS_DIR / Path(email[0])).read_bytes(),
        email[1],
    )
    for email in EMAIL_ASSET_NAMES
]


def bytes_generator(data: bytes) -> Generator[bytes, None, None]:
    yield data


@pytest.fixture()
def rspamd_service() -> RspamdService:
    return get_rspamd_service()


@pytest.mark.parametrize("_, email, is_spam", EMAIL_ASSETS)
def test_detect_spam_from_generator(
    rspamd_service: RspamdService,
    _: Path,
    email: bytes,
    is_spam: bool,
):
    spam_detected = rspamd_service.detect_spam_from_generator(bytes_generator(email))
    assert spam_detected is is_spam
