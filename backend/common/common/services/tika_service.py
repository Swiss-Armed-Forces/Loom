"""
tika parser proxy on docker image
https://github.com/apache/tika-docker
https://github.com/chrismattmann/tika-python
https://cwiki.apache.org/confluence/display/TIKA/TikaServer
http://blog.marcoreis.net/text-extraction-and-ocr-with-apache-tika/
https://cwiki.apache.org/confluence/display/TIKA/TikaOCR

"""

import csv
import logging
from contextlib import contextmanager
from tempfile import TemporaryFile
from typing import Generator, Mapping
from zipfile import Path as ZipPath
from zipfile import ZipFile

import requests
from pydantic import BaseModel, ConfigDict
from requests import HTTPError

from common.services.lazybytes_service import LazyBytes, LazyBytesService
from common.settings import settings

TIKA_TIMEOUT_SECONDS = 1200
TIKA_METADATA_JOIN_CHAR = ","
TIKA_SPOOLED_MAX_SIZE = int(1 * (1024**2))  # 1 MiB
TIKA_UNPACK_MAX_SIZE = int(512 * (1024**2))  # 512 MiB
TIKA_MAX_TEXT_SIZE = int(2 * (1024**2))  # 2 MiB
TIKA_VERIFY_TLS = False

logger = logging.getLogger(__name__)


class TikaAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    data: LazyBytes


class TikaResult(BaseModel):
    """Tika Parser result."""

    text: LazyBytes | None = None
    text_truncated: bool = False
    meta: dict = {}
    attachments: list[TikaAttachment] = []


class TikaError(Exception):
    """Tika Parser exception."""


class TikaService:
    """Tika parser."""

    def __init__(
        self,
        lazybytes_service: LazyBytesService,
        timeout: int = TIKA_TIMEOUT_SECONDS,
    ):
        self.timeout = timeout
        self.lazybytes_service = lazybytes_service

    @contextmanager
    def _unpack(self, data: memoryview) -> Generator[ZipFile, None, None]:
        """Returns the tika unpack result."""
        uri = f"{settings.tika_server_host}/unpack/all"
        headers: Mapping[str, str] = {
            # See comment below why this is commented here
            # 'Accept': 'application/x-tar',
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
            "X-Tika-OCRLanguage": "+".join(settings.tika_ocr_languages),
            "unpackMaxBytes": str(TIKA_UNPACK_MAX_SIZE),
        }
        response = requests.put(
            uri,
            data,
            headers=headers,
            stream=True,
            timeout=self.timeout,
            verify=TIKA_VERIFY_TLS,
        )

        response.raise_for_status()

        # Note: we should use SpooledTemporaryFile, but in our python version
        # SpooledTemporaryFile does not implement the full io.BufferedIOBase
        # interface. Hence certain operations used by ZipFile will fail.
        # This should be fixed with python > 3.11
        # Reference:
        # - https://docs.python.org/3.11/whatsnew/3.11.html#tempfile
        #
        # Use the following:
        #
        # with SpooledTemporaryFile(
        #    max_size=TIKA_SPOOLED_MAX_SIZE, dir=settings.tempfile_dir
        # ) as zipfd:
        with TemporaryFile(dir=settings.tempfile_dir) as zipfd:
            for content in response.iter_content(TIKA_SPOOLED_MAX_SIZE):
                zipfd.write(content)
            zipfd.flush()
            zipfd.seek(0)
            with ZipFile(zipfd) as zipfile:
                yield zipfile

    def _parse(self, zipfile: ZipFile) -> TikaResult:
        result = TikaResult()

        for name in zipfile.namelist():
            match name:
                case "__METADATA__":
                    with ZipPath(zipfile, name).open(mode="r", newline="") as zipfd:
                        for metadata_line in csv.reader(zipfd):
                            metadata_key = metadata_line[0]
                            metadata_value = metadata_line[1:]
                            if len(metadata_value) == 1:
                                result.meta[metadata_key] = metadata_value[0]
                            else:
                                result.meta[metadata_key] = metadata_value
                case "__TEXT__":
                    with ZipPath(zipfile, name).open(mode="rb") as zipfd:
                        text = zipfd.read(TIKA_MAX_TEXT_SIZE)
                        result.text = self.lazybytes_service.from_bytes(text)
                        result.text_truncated = len(text) >= TIKA_MAX_TEXT_SIZE
                case _:
                    with ZipPath(zipfile, name).open(mode="rb") as zipfd:
                        result.attachments.append(
                            TikaAttachment(
                                name=name,
                                data=self.lazybytes_service.from_bytes(zipfd.read()),
                            )
                        )

        return result

    def parse(self, data: memoryview) -> TikaResult:
        """Parse file using tika.

        Raises TikaError on failures.
        """
        if len(data) <= 0:
            return TikaResult()

        try:
            with self._unpack(data) as zipfile:
                return self._parse(zipfile)
        except HTTPError as exc:
            raise TikaError from exc

    def get_language(self, data: memoryview) -> str:
        """Returns the language."""
        if len(data) <= 0:
            return ""

        uri = f"{settings.tika_server_host}/language/string"
        headers: Mapping[str, str] = {
            "Accept": "text/plain",
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
        }
        response = requests.put(
            uri, data, headers=headers, timeout=self.timeout, verify=TIKA_VERIFY_TLS
        )
        response.raise_for_status()
        return response.text

    def get_file_type(self, data: memoryview) -> str:
        """Returns the filetype."""
        if len(data) <= 0:
            return ""

        uri = f"{settings.tika_server_host}/detect/stream"
        headers: Mapping[str, str] = {
            "Accept": "text/plain",
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
        }
        response = requests.put(
            uri, data, headers=headers, timeout=self.timeout, verify=TIKA_VERIFY_TLS
        )
        response.raise_for_status()
        return response.text
