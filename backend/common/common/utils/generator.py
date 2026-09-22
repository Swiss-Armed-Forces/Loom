import itertools
from io import RawIOBase
from typing import Iterator, NamedTuple


class ByteCountResult(NamedTuple):
    """Result of a bytecount check together with the still unconsumed datastream."""

    is_lte: bool
    datastream: Iterator[bytes]


def bytecount_lte(datastream: Iterator[bytes], *, limit: int) -> ByteCountResult:
    """Checks if the bytecount of the given datastream is less than or equal to the
    given limit.

    itertools.tee is used to create two independent copies of the stream. One stream
    remains untouched and is returned to the caller and the other one is consumed here.
    The original datastream is consumed and can no longer be used.

    A negative limit can never be satisfied, so in that case the datastream is returned
    as is, without teeing it. A tee branch pins a whole block of already yielded chunks
    in memory (CPython buffers 57 items per block), which for the megabyte sized chunks
    the crawler streams means tens of megabytes retained for the lifetime of the stream.
    """
    if limit < 0:
        return ByteCountResult(False, datastream)
    work_datastream, orig_data_stream = itertools.tee(datastream)
    consumed = 0
    for chunk in work_datastream:
        consumed += len(chunk)
        if consumed > limit:
            return ByteCountResult(False, orig_data_stream)
    return ByteCountResult(True, orig_data_stream)


class FileLikeStream(RawIOBase):
    """File like wrapper for streams.

    This class exists because the minio client need the read() method to upload the
    data.

    read() never accumulates more than a single chunk of the wrapped stream. As a raw
    stream it is allowed to return fewer bytes than requested, so callers asking for a
    large block (minio asks for a full multipart part) get served chunk by chunk instead
    of the whole block being materialised here first.
    """

    def __init__(self, stream: Iterator[bytes]):
        self._stream = stream
        self._chunk = b""
        self._offset = 0

    def readable(self) -> bool:
        return True

    def _fill(self) -> None:
        """Pull chunks until one holds unread data or the stream is exhausted.

        Empty chunks are skipped: to a caller an empty read signals EOF, so an empty
        chunk in the middle of the stream must not be passed on.
        """
        while self._offset >= len(self._chunk):
            # None is the exhaustion sentinel: b"" is a valid chunk, not an EOF marker.
            chunk = next(self._stream, None)
            if chunk is None:
                return
            self._chunk = chunk
            self._offset = 0

    def readall(self) -> bytes:
        chunks = [self._chunk[self._offset :], *self._stream]
        self._chunk = b""
        self._offset = 0
        return b"".join(chunks)

    def read(self, size: int = -1, /) -> bytes:
        # Return everything.
        if size is None or size < 0:
            return self.readall()

        if size == 0:
            return b""

        self._fill()
        end = min(self._offset + size, len(self._chunk))
        out = self._chunk[self._offset : end]
        self._offset = end

        # Drop the chunk as soon as it is drained so it is not held until the next read.
        if self._offset >= len(self._chunk):
            self._chunk = b""
            self._offset = 0

        return out
