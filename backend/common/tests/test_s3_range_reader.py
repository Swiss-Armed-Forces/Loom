import io
import zipfile
from unittest.mock import MagicMock

import pytest
from minio import Minio

from common.services.s3_range_reader import S3RangeReader

BUCKET = "loom-file-storage"
OBJECT = "5f2b1c3d-0000-4000-8000-000000000001"


class _FakeResponse:
    """What minio's get_object hands back: a urllib3-ish response."""

    def __init__(self, payload: bytes):
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class _ObjectStore:
    """Serves real byte ranges out of an in-memory object, and counts requests."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.responses: list[_FakeResponse] = []

    def get_object(
        self, bucket: str, object_name: str, offset: int = 0, length: int = 0
    ):
        assert bucket == BUCKET
        assert object_name == OBJECT
        end = offset + length if length else len(self.payload)
        response = _FakeResponse(self.payload[offset:end])
        self.responses.append(response)
        return response


def _reader_for(payload: bytes) -> tuple[S3RangeReader, _ObjectStore]:
    store = _ObjectStore(payload)
    client = MagicMock(spec=Minio)
    client.get_object.side_effect = store.get_object
    return S3RangeReader(client, BUCKET, OBJECT, len(payload)), store


@pytest.mark.parametrize("whence", [io.SEEK_SET, io.SEEK_CUR, io.SEEK_END])
def test_seeks_clamp_inside_the_object(whence: int):
    reader, _ = _reader_for(b"0123456789")

    reader.seek(-9999, whence)

    assert reader.tell() == 0


def test_reads_across_block_boundaries():
    payload = bytes(range(256)) * 1024
    reader, _ = _reader_for(payload)

    reader.seek(100_000)

    assert reader.read(1024) == payload[100_000:101_024]


def test_read_at_eof_returns_empty():
    reader, _ = _reader_for(b"short")

    reader.seek(0, io.SEEK_END)

    assert reader.read(16) == b""


def test_an_invalid_whence_is_rejected():
    reader, _ = _reader_for(b"0123456789")

    with pytest.raises(ValueError):
        reader.seek(0, 99)


def test_every_response_is_closed_and_released():
    """A leaked connection is invisible until the pool runs dry under load."""
    reader, store = _reader_for(bytes(range(256)) * 1024)

    reader.read(4096)

    assert store.responses
    assert all(r.closed and r.released for r in store.responses)


def test_a_zip_member_is_read_without_transferring_the_object():
    """The whole point: structure is reachable without moving the body.

    The filler is stored uncompressed and pseudo-random, because a compressible member
    would deflate away and prove nothing about the read volume.
    """
    filler = (bytes(range(256)) * 16_000)[:4_000_000]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as zip_file:
        zip_file.writestr("meta.json", b'{"hello": "world"}')
        zip_file.writestr("big.bin", filler)
    payload = buffer.getvalue()
    assert len(payload) > 1_000_000  # the stored member really is large

    reader, store = _reader_for(payload)

    with zipfile.ZipFile(io.BufferedReader(reader)) as zip_file:  # type: ignore[arg-type]
        assert zip_file.read("meta.json") == b'{"hello": "world"}'

    fetched = sum(len(response.read()) for response in store.responses)
    assert fetched < len(payload) // 4, f"read {fetched} of {len(payload)} bytes"
