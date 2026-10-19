import io
import zipfile
from dataclasses import dataclass

import pytest
from minio.error import S3Error

from common.services.s3_range_reader import BLOCK_SIZE, S3RangeReader
from common.testing.s3_doubles import ObjectStore, s3_serving

BUCKET = "loom-file-storage"
OBJECT = "5f2b1c3d-0000-4000-8000-000000000001"


@dataclass(frozen=True)
class _Subject:
    reader: S3RangeReader
    store: ObjectStore


def _reader_for(payload: bytes) -> _Subject:
    double = s3_serving(payload, BUCKET, OBJECT)
    return _Subject(
        reader=S3RangeReader(double.client, BUCKET, OBJECT, len(payload)),
        store=double.store,
    )


@pytest.mark.parametrize("whence", [io.SEEK_SET, io.SEEK_CUR, io.SEEK_END])
def test_seeks_clamp_inside_the_object(whence: int):
    reader = _reader_for(b"0123456789").reader

    reader.seek(-9999, whence)

    assert reader.tell() == 0


def test_reads_across_block_boundaries():
    payload = bytes(range(256)) * 1024
    reader = _reader_for(payload).reader

    reader.seek(100_000)

    assert reader.read(1024) == payload[100_000:101_024]


def test_read_at_eof_returns_empty():
    reader = _reader_for(b"short").reader

    reader.seek(0, io.SEEK_END)

    assert reader.read(16) == b""


def test_a_range_starting_past_the_end_never_reaches_the_client():
    """What the clamp in `fetch_range` is for.

    Real object storage answers a range at or past the object's end with `InvalidRange`
    (HTTP 416), not with an empty body -- so an unclamped probe would raise against
    SeaweedFS while passing against a double that simply slices.
    """
    subject = _reader_for(b"0123456789")

    assert subject.reader.fetch_range(10, 4) == b""
    assert subject.reader.fetch_range(9999, 4) == b""
    assert subject.store.request_count == 0


def test_an_empty_object_is_never_range_requested():
    """The shape the crawler prescreen meets for real: a zero-byte intake object."""
    subject = _reader_for(b"")

    assert subject.reader.fetch_range(0, 7) == b""
    assert subject.store.request_count == 0


def test_the_double_refuses_an_unsatisfiable_range_like_real_storage():
    """Pin the double's behaviour, since the clamp above is only tested through it."""
    double = s3_serving(b"0123456789", BUCKET, OBJECT)

    with pytest.raises(S3Error):
        double.store.get_object(BUCKET, OBJECT, offset=10, length=4)


def test_an_invalid_whence_is_rejected():
    reader = _reader_for(b"0123456789").reader

    with pytest.raises(ValueError):
        reader.seek(0, 99)


def test_every_response_is_closed_and_released():
    """A leaked connection is invisible until the pool runs dry under load."""
    subject = _reader_for(bytes(range(256)) * 1024)

    subject.reader.read(4096)

    assert subject.store.every_response_was_released


def test_a_read_larger_than_a_block_is_not_cached():
    """`zipfile` reads the whole central directory in one call.

    On a 200k-file archive that is ~40 MB, and caching it would hold it in the
    crawler pod -- plus a second copy in the slice and a third in the caller's
    buffer -- for every zip-shaped object a USB mirror lands in the bucket.
    """
    payload = (bytes(range(256)) * 2048)[: BLOCK_SIZE * 4]
    subject = _reader_for(payload)

    wanted = BLOCK_SIZE * 3
    buffer = bytearray(wanted)
    assert subject.reader.readinto(buffer) == wanted
    assert bytes(buffer) == payload[:wanted]

    # The whole read came back, and none of it was kept.
    assert subject.store.fetched_bytes == wanted
    assert len(subject.reader.read(1)) == 1


def test_a_small_read_still_fetches_one_block():
    """The other half of the same rule: tiny reads must not be one request each."""
    payload = (bytes(range(256)) * 2048)[: BLOCK_SIZE * 4]
    subject = _reader_for(payload)

    subject.reader.read(16)
    subject.reader.read(16)

    assert len(subject.store.responses) == 1
    assert subject.store.fetched_bytes == BLOCK_SIZE


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

    subject = _reader_for(payload)

    with zipfile.ZipFile(io.BufferedReader(subject.reader)) as zip_file:  # type: ignore[arg-type]
        assert zip_file.read("meta.json") == b'{"hello": "world"}'

    fetched = subject.store.fetched_bytes
    assert fetched < len(payload) // 4, f"read {fetched} of {len(payload)} bytes"
