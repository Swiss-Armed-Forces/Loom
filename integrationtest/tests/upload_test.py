import tarfile
import time
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import requests
from common.utils.random_file import random_file, random_file_printable
from requests_toolbelt import MultipartEncoder
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE, TIKA_UNPACK_MAX_SIZE

from utils.consts import ASSETS_DIR, FILES_ENDPOINT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset

# Traefik v3 default readTimeout for HTTP entrypoints.
# See traefik/values.yaml – ports.web/websecure.transport.respondingTimeouts.readTimeout
_TRAEFIK_DEFAULT_READ_TIMEOUT_SECONDS = 60


class _ThrottledBytesIO:
    """File-like wrapper that delays the first ``read()`` call by ``upload_duration``
    seconds.

    When passed as the file body to ``requests``, the HTTP headers are sent immediately
    but the body bytes are withheld until the sleep ends.  Traefik receives the request
    headers and starts its ``readTimeout`` clock; if the timeout fires before the sleep
    ends the connection is dropped.
    """

    def __init__(self, data: bytes, upload_duration: float) -> None:
        self._data = data
        self._pos = 0
        self._upload_duration = upload_duration
        self._started = False

    @property
    def len(self) -> int:
        return len(self._data) - self._pos

    def read(self, size: int = -1) -> bytes:
        if not self._started:
            self._started = True
            time.sleep(self._upload_duration)
        if size < 0:
            chunk = self._data[self._pos :]
            self._pos = len(self._data)
        else:
            chunk = self._data[self._pos : self._pos + size]
            self._pos += len(chunk)
        return chunk


def test_upload_email():
    upload_asset("basic_email.eml")

    file = get_file_preview_by_name("basic_email.eml")

    assert not file.hidden
    assert file.file_extension == ".eml"
    assert file.path == "//api-upload/basic_email.eml"


def test_upload_email_with_attachment():
    upload_asset("attachment_content_disposition.eml")

    attachment = get_file_preview_by_name("api.rb")

    assert attachment.path == "//api-upload/attachment_content_disposition.eml/api.rb"
    assert "Hello, world!" in attachment.content


@pytest.mark.flaky(reruns=3)
def test_upload_mbox_email_with_attachment():
    upload_asset("attachment_pdf.eml")

    mail = get_file_preview_by_name("attachment_pdf.eml")
    mail_content = get_file_preview_by_name("0.eml")
    attachment = get_file_preview_by_name("broken.pdf")

    assert mail.file_extension == ".eml"
    assert attachment.file_extension == ".pdf"
    assert "Just attaching" in mail_content.content


def test_upload_png():
    upload_asset("1.png")

    file = get_file_preview_by_name("1.png")

    assert not file.hidden
    assert file.file_extension == ".png"
    assert file.path == "//api-upload/1.png"


def test_upload_pdf():
    upload_asset("home.pdf")

    file = get_file_preview_by_name("home.pdf")

    assert not file.hidden
    assert file.file_extension == ".pdf"
    assert file.path == "//api-upload/home.pdf"


def test_upload_zip_archive():
    """Upload archive.zip and expect its content, file.txt to be extracted and
    indexed."""
    upload_asset("archive.zip")

    file = get_file_preview_by_name("file.txt")

    assert not file.hidden
    assert file.path == "//api-upload/archive.zip/file.txt"
    assert "content of a file" in file.content


def test_upload_tar_gz_archive():
    """Upload archive.zip and expect its content, file.txt to be extracted and
    indexed."""
    upload_asset("archive.tar.gz")

    file = get_file_preview_by_name("emptyfile")

    assert not file.hidden
    assert file.path == "//api-upload/archive.tar.gz/0/emptyfile"
    assert "You found me!" in file.content


def test_quotation_marks_in_file_name():
    upload_asset('".zip')

    file = get_file_preview_by_name('".zip')

    assert file.path == "//api-upload/%22.zip"


@pytest.mark.skip(
    reason="This test leads to java.lang.OutOfMemoryError: Java heap space in tika"
)
@pytest.mark.parametrize(
    "random_file_printable_size",
    [TIKA_MAX_TEXT_SIZE, TIKA_UNPACK_MAX_SIZE],
)
def test_upload_large_text_file(random_file_printable_size: int):
    with random_file_printable(ASSETS_DIR, random_file_printable_size) as fd:
        name = Path(fd.name).name
        upload_asset(name, request_timeout=300)

    get_file_preview_by_name(
        name, max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE * 20
    )


@pytest.mark.skip(reason="This test crashes elasticsearch on the CI/CD runner")
@pytest.mark.parametrize("random_file_size", [TIKA_UNPACK_MAX_SIZE + 1])
def test_upload_very_large_tar_file(random_file_size: int, tmp_path):
    with NamedTemporaryFile(mode="wb", dir=ASSETS_DIR) as tmp:
        with tarfile.open(fileobj=tmp, mode="w") as tar:
            with random_file(tmp_path, random_file_size) as fd:
                tarinfo = tar.gettarinfo(arcname="largefile", fileobj=fd)
                tar.addfile(tarinfo, fd)
        tmp.flush()
        upload_asset(tmp.name, request_timeout=300)

    # check to see if extraction was successful
    get_file_preview_by_name("largefile", max_wait_time_per_file=600)


@pytest.mark.skip(reason="This test crashes elasticsearch on the CI/CD runner")
@pytest.mark.parametrize("random_file_size", [TIKA_UNPACK_MAX_SIZE + 1])
def test_upload_very_large_zip_file(random_file_size: int, tmp_path):
    with NamedTemporaryFile(mode="wb", dir=ASSETS_DIR) as tmp:
        with zipfile.ZipFile(tmp, "w") as archive:
            with random_file(tmp_path, random_file_size) as fd:
                archive.write(fd.name, "largefile")
        tmp.flush()
        upload_asset(tmp.name, request_timeout=300)

    # check to see if extraction was successful
    get_file_preview_by_name("largefile", max_wait_time_per_file=600)


def test_upload_empty_file():
    with NamedTemporaryFile(mode="w", dir=ASSETS_DIR) as tmp:
        tmp.flush()
        name = Path(tmp.name).name
        upload_asset(name, request_timeout=300)

    get_file_preview_by_name(name)


def test_upload_large_file_does_not_timeout():
    """Upload whose body transfer spans longer than Traefik's default readTimeout must
    succeed.

    Traefik v3 defaults entrypoint readTimeout to 60 s.  Without an explicit
    override, any upload that takes longer than one minute is silently dropped.
    This test reproduces the failure by delaying the first body read so that
    the total transfer time exceeds the default, then asserting the server
    returns 202.

    Fix: set readTimeout to "0s" on the web and websecure entrypoints in
    traefik/values.yaml (ports.web/websecure.transport.respondingTimeouts.readTimeout).
    """
    upload_duration = _TRAEFIK_DEFAULT_READ_TIMEOUT_SECONDS + 5

    throttled = _ThrottledBytesIO(b"x" * 1024, upload_duration=upload_duration)
    encoder = MultipartEncoder(
        {"file": ("slow_upload.bin", throttled, "application/octet-stream")}
    )
    response = requests.post(
        FILES_ENDPOINT,
        data=encoder,
        headers={"Content-Type": encoder.content_type},
        timeout=upload_duration + 30,
    )
    assert response.status_code == 202
