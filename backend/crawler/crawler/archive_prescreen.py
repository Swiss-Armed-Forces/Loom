"""Deciding what an intake object is, without downloading it.

The crawler is the only component that holds an S3 client pointed at the object while it
is still in the bucket, and that is what makes an exact answer cheap here and expensive
everywhere else: `FileStorageLazyBytesService.load_file` spools the whole object into a
temporary file before anything can look at it, so content-inspecting every crawled file
after materialising it would double every transfer.

Instead the object is wrapped in a seekable reader that turns `read`/`seek` into HTTP
range requests. `zipfile` then does what it always does -- read the end-of-central-
directory record from the tail, parse the central directory, inflate one member -- and
touches a few tens of kilobytes of a 50 GB archive. Delegating to the stdlib this way is
also why zip64, archive comments and oddly-aligned central directories need no special
handling here.

The classification itself is `common.archive.archive_detection`, the very function the
worker's `detect_loom_archive` task uses, so the two can never disagree about what a
loom archive is.
"""

import io
import logging
from enum import StrEnum

from common.archive.archive_detection import (
    ENCRYPTED_ARCHIVE_MAGIC,
    is_encrypted_archive_header,
    is_loom_archive,
)
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

# How much to fetch per underlying request. zipfile issues many small reads
# (record headers are tens of bytes), and one HTTP request each would turn a
# cheap classification into hundreds of round trips. 64 KiB also comfortably
# covers the end-of-central-directory record plus a maximal 64 KiB archive
# comment, so the tail is almost always a single request.
_BLOCK_SIZE = 64 * 1024


class IntakeObjectKind(StrEnum):
    """What a crawled intake object turned out to be."""

    PLAIN_FILE = "plain_file"
    LOOM_ARCHIVE = "loom_archive"
    LOOM_ARCHIVE_ENCRYPTED = "loom_archive_encrypted"


class S3RangeReader(io.RawIOBase):
    """A seekable, read-only file object backed by S3 range requests.

    Only the handful of methods `zipfile` needs are implemented. Reads are served from a
    single cached block, which is what keeps the request count down without holding the
    object in memory.
    """

    def __init__(self, client: Minio, bucket: str, object_name: str, size: int):
        super().__init__()
        self._client = client
        self._bucket = bucket
        self._object_name = object_name
        self._size = size
        self._pos = 0
        self._block = b""
        self._block_start = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        match whence:
            case io.SEEK_SET:
                target = offset
            case io.SEEK_CUR:
                target = self._pos + offset
            case io.SEEK_END:
                target = self._size + offset
            case _:
                raise ValueError(f"invalid whence: {whence}")

        # zipfile seeks backwards from the end looking for the central
        # directory; clamping rather than raising keeps that probing cheap.
        self._pos = max(0, min(target, self._size))
        return self._pos

    def _fetch(self, offset: int, length: int) -> bytes:
        response = self._client.get_object(
            self._bucket, self._object_name, offset=offset, length=length
        )
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def readinto(self, buffer) -> int:  # type: ignore[override]
        wanted = len(buffer)
        if wanted == 0 or self._pos >= self._size:
            return 0

        wanted = min(wanted, self._size - self._pos)

        if not self._block_start <= self._pos < self._block_start + len(self._block):
            block_length = min(max(wanted, _BLOCK_SIZE), self._size - self._pos)
            self._block = self._fetch(self._pos, block_length)
            self._block_start = self._pos
            if not self._block:
                return 0

        start = self._pos - self._block_start
        chunk = self._block[start : start + wanted]
        buffer[: len(chunk)] = chunk
        self._pos += len(chunk)
        return len(chunk)


def classify_intake_object(
    client: Minio, bucket: str, object_name: str, size: int
) -> IntakeObjectKind:
    """Decide whether an intake object is a loom archive, plain or encrypted.

    Falls back to `PLAIN_FILE` on anything unexpected. That direction matters: a plain
    file misrouted to the archive pipeline used to be discarded without a trace, whereas
    an archive misrouted to the ordinary indexing pipeline is merely indexed as the zip
    it is. Degrade towards the recoverable mistake.
    """
    try:
        # BufferedReader for two reasons: it coalesces zipfile's many tiny reads
        # on top of the block cache below, and it is what makes this a plain
        # binary file object as far as ZipFile and mypy are concerned.
        with io.BufferedReader(
            S3RangeReader(client, bucket, object_name, size)
        ) as source:
            if is_encrypted_archive_header(source.read(len(ENCRYPTED_ARCHIVE_MAGIC))):
                return IntakeObjectKind.LOOM_ARCHIVE_ENCRYPTED

            source.seek(0)
            if is_loom_archive(source):
                return IntakeObjectKind.LOOM_ARCHIVE
    # Deliberately not a bare `except Exception`: pylint's broad-exception-caught
    # is enabled, and these are the failures that actually reach here. A genuinely
    # exotic transport error propagates to the caller, which leaves the object
    # unmarked so the next poll retries it.
    except (OSError, ValueError, S3Error):
        logger.warning(
            "Could not classify intake object '%s'; treating it as a plain file",
            object_name,
            exc_info=True,
        )

    return IntakeObjectKind.PLAIN_FILE
