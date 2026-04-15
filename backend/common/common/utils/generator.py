import itertools
from io import RawIOBase
from typing import Iterator


def bytecount_lte(
    datastream: Iterator[bytes], *, limit: int
) -> tuple[bool, Iterator[bytes]]:
    """Checks if the bytecount of the given datastream is less than or equal to the
    given limit.

    itertools.tee is used to create two independent copies of the stream. One stream
    remains untouched and is returned to the caller and the other one is consumed here.
    The original datastream is consumed and can no longer be used.
    """
    work_datastream, orig_data_stream = itertools.tee(datastream)
    if limit < 0:
        return False, orig_data_stream
    consumed = 0
    for chunk in work_datastream:
        consumed += len(chunk)
        if consumed > limit:
            return False, orig_data_stream
    return True, orig_data_stream


class FileLikeStream(RawIOBase):
    """File like wrapper for streams.

    This class exists because the minio client need the read() method to upload the
    data.
    """

    def __init__(self, stream: Iterator[bytes]):
        self._stream = stream
        self._buffer = b""

    def read(self, size: int = -1, /) -> bytes:
        # Return everything.
        if size is None or size < 0:
            data = self._buffer + b"".join(self._stream)
            self._buffer = b""
            return data

        # Try to satisfy request from buffer first.
        while len(self._buffer) < size:
            try:
                chunk = next(self._stream)
                self._buffer += chunk
            except StopIteration:
                break

        # Extract the requested size and save the remainder.
        out = self._buffer[:size]
        self._buffer = self._buffer[size:]

        return out
