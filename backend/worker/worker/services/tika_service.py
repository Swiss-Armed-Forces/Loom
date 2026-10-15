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
from itertools import chain
from tempfile import TemporaryFile
from typing import Generator, Iterable, Mapping
from zipfile import BadZipFile
from zipfile import Path as ZipPath
from zipfile import ZipFile

import requests
from common.file.file_repository import TikaMeta
from common.services.lazybytes_service import TempLazyBytes, TempLazyBytesService
from pydantic import BaseModel, ConfigDict, Field
from requests import HTTPError, RequestException

from worker.settings import settings

TIKA_METADATA_JOIN_CHAR = ","
TIKA_SPOOLED_MAX_SIZE = int(1 * (1024**2))  # 1 MiB
TIKA_UNPACK_MAX_SIZE = int(512 * (1024**2))  # 512 MiB
TIKA_MAX_TEXT_SIZE = int(2 * (1024**2))  # 2 MiB
TIKA_VERIFY_TLS = False

# Status codes on which tika-server reports that it understood the request and
# refused this particular document: an unsupported media type, an encrypted or
# corrupt file, a malformed request. Every attempt fails the same way.
TIKA_PERMANENT_STATUS_CODES = frozenset({400, 405, 415, 422})

logger = logging.getLogger(__name__)


class TikaAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    data: TempLazyBytes


class TikaResult(BaseModel):
    """Tika Parser result."""

    text: TempLazyBytes | None = None
    text_truncated: bool = False
    meta: TikaMeta = Field(default_factory=TikaMeta)
    attachments: list[TikaAttachment] = []


class TikaError(Exception):
    """Tika Parser exception."""


class TikaTransientError(TikaError):
    """Tika failed in a way a later attempt may survive.

    A saturated fork pool, a full /tmp, a parser JVM killed by the task timeout: the
    document is fine, the server was not. Only this type belongs in a task's
    ``autoretry_for``.
    """


class TikaPermanentError(TikaError):
    """Tika understood the request and refused this document.

    Encrypted, corrupt, or of an unsupported media type. Retrying costs a full backoff
    budget and ends in the same place, so callers degrade on the first attempt.
    """


def classify_tika_http_error(exc: HTTPError) -> TikaError:
    """Map an HTTP status from tika-server onto the transient/permanent split.

    An unrecognised status counts as transient: mistaking a permanent failure for a
    transient one costs one wasted retry budget, while the reverse silently degrades a
    document to a fallback extractor.
    """
    status_code = exc.response.status_code if exc.response is not None else None
    if status_code in TIKA_PERMANENT_STATUS_CODES:
        return TikaPermanentError(f"tika refused the document: HTTP {status_code}")
    return TikaTransientError(f"tika call failed: HTTP {status_code}")


@contextmanager
def _as_tika_error() -> Generator[None, None, None]:
    """Translate everything the transport can raise into the TikaError hierarchy."""
    try:
        yield
    except HTTPError as exc:
        raise classify_tika_http_error(exc) from exc
    except BadZipFile as exc:
        # A 200 whose body is not a zip, or one cut short. tika only writes a truncated
        # archive when the parse it was streaming died underneath it.
        raise TikaTransientError("tika returned a truncated or non-zip body") from exc
    except RequestException as exc:
        # Connect or read timeout, broken chunked encoding, DNS failure, reset peer.
        raise TikaTransientError("tika request failed") from exc


class TikaService:
    """Tika parser."""

    def __init__(
        self,
        lazybytes_service: TempLazyBytesService,
        timeout: int,
    ):
        self.timeout = timeout
        self.lazybytes_service = lazybytes_service

    def _peek_and_chain(
        self, data_generator: Generator[bytes, None, None]
    ) -> Iterable[bytes] | None:
        """Peek at the first chunk of a generator and chain it back.

        Returns None if the generator is empty, otherwise returns an iterable with the
        first chunk chained back to the rest of the generator.
        """
        try:
            first_chunk = next(data_generator)
        except StopIteration:
            return None
        return chain([first_chunk], data_generator)

    @contextmanager
    def _unpack(self, data_iterable: Iterable[bytes]) -> Generator[ZipFile, None, None]:
        """Returns the tika unpack result."""
        uri = f"{str(settings.tika_server_host).rstrip('/')}/unpack/all"
        headers: Mapping[str, str] = {
            # See comment below why this is commented here
            # 'Accept': 'application/x-tar',
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
            "X-Tika-OCRLanguage": "+".join(settings.tika_ocr_languages),
            # requests sends chunked bodies without a Content-Type, which makes
            # tika (CXF) fall back to application/x-www-form-urlencoded and pick
            # the EmptyParser: no OCR, empty content for scanned documents.
            # octet-stream tells tika to auto-detect the type instead.
            "Content-Type": "application/octet-stream",
            "unpackMaxBytes": str(TIKA_UNPACK_MAX_SIZE),
        }
        response = requests.put(
            uri,
            data_iterable,
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
                    # Collect all metadata into a dictionary
                    metadata_dict = {}
                    with ZipPath(zipfile, name).open(mode="r", newline="") as zipfd:
                        for metadata_line in csv.reader(zipfd):
                            metadata_key = metadata_line[0]
                            metadata_value = metadata_line[1:]
                            metadata_dict[metadata_key] = (
                                # flatten if possible
                                metadata_value[0]
                                if len(metadata_value) == 1
                                else metadata_value
                            )
                    # Use model_validate to properly handle aliases
                    result.meta = TikaMeta.model_validate(metadata_dict)
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
                                data=self.lazybytes_service.from_file(zipfd),
                            )
                        )

        return result

    def parse_from_generator(
        self, data_generator: Generator[bytes, None, None]
    ) -> TikaResult:
        """Parse file using tika.

        Raises TikaTransientError or TikaPermanentError on failures.
        """
        data_iterable = self._peek_and_chain(data_generator)
        if data_iterable is None:
            return TikaResult()

        with _as_tika_error():
            with self._unpack(data_iterable) as zipfile:
                return self._parse(zipfile)

    def get_language_from_generator(
        self, data_generator: Generator[bytes, None, None]
    ) -> str:
        """Detect the document language.

        Raises TikaTransientError or TikaPermanentError on failures.
        """
        data_iterable = self._peek_and_chain(data_generator)
        if data_iterable is None:
            return ""

        uri = f"{str(settings.tika_server_host).rstrip('/')}/language/string"
        headers: Mapping[str, str] = {
            "Accept": "text/plain",
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
        }
        with _as_tika_error():
            response = requests.put(
                uri,
                data_iterable,
                headers=headers,
                timeout=self.timeout,
                verify=TIKA_VERIFY_TLS,
            )
            response.raise_for_status()
            return response.text

    def get_file_type_from_generator(
        self, data_generator: Generator[bytes, None, None]
    ) -> str:
        """Detect the document media type.

        Raises TikaTransientError or TikaPermanentError on failures.
        """
        data_iterable = self._peek_and_chain(data_generator)
        if data_iterable is None:
            return ""

        uri = f"{str(settings.tika_server_host).rstrip('/')}/detect/stream"
        headers: Mapping[str, str] = {
            "Accept": "text/plain",
            "X-Tika-Timeout-Millis": str(self.timeout * 1000**1),
        }
        with _as_tika_error():
            response = requests.put(
                uri,
                data_iterable,
                headers=headers,
                timeout=self.timeout,
                verify=TIKA_VERIFY_TLS,
            )
            response.raise_for_status()
            return response.text
