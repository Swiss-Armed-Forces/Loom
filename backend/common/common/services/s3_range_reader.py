"""A seekable file object over an S3 object, backed by range requests.

This exists so that structure can be inspected without transferring content.
`LazyBytesService.load_file` spools the whole object into a temporary file before
anything can look at it, which is the right primitive for handing a real file to an
external tool and the wrong one for answering "is this a zip?" -- on a several-hundred
gigabyte archive it costs a full download and a full local copy to read a few bytes.

Wrapped in this reader, `zipfile` does what it always does -- read the end-of-central-
directory record from the tail, parse the central directory, inflate one member -- and
touches a few tens of kilobytes. Delegating to the stdlib this way is also why zip64,
archive comments and oddly-aligned central directories need no special handling.

Two callers, deliberately from opposite sides: `LazyBytesService.load_seekable` uses it
for objects already in file storage, and `crawler.archive_prescreen` uses it directly
against a raw client for an intake object that is not a `LazyBytes` at all.
"""

import io

from minio import Minio

# How much to fetch per underlying request. zipfile issues many small reads
# (record headers are tens of bytes), and one HTTP request each would turn a
# cheap inspection into hundreds of round trips. 64 KiB also comfortably
# covers the end-of-central-directory record plus a maximal 64 KiB archive
# comment, so the tail is almost always a single request.
BLOCK_SIZE = 64 * 1024


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
            block_length = min(max(wanted, BLOCK_SIZE), self._size - self._pos)
            self._block = self._fetch(self._pos, block_length)
            self._block_start = self._pos
            if not self._block:
                return 0

        start = self._pos - self._block_start
        chunk = self._block[start : start + wanted]
        buffer[: len(chunk)] = chunk
        self._pos += len(chunk)
        return len(chunk)
