import random

import pytest

from common.utils.generator import FileLikeStream, bytecount_lte
from tests.lazybytes_service_test import data_generator


def dummy_data_generator(total_bytes: int, chunk_size: int = 1):
    """Yields random data in 'chunk_size' increments."""
    generated = 0
    while generated < total_bytes:
        yield random.randbytes(chunk_size)
        generated += chunk_size


def test_bytecount_lte_does_not_consume_stream():
    """Test that _bytecount_lte evaluates the size without losing elements from the
    stream."""
    original_data = b"0123456789xx"
    stream = data_generator(original_data)
    next(stream)  # Stream points at b'1'

    # Test over limit (limit 5 bytes, stream is 12 bytes)
    is_lte, stream = bytecount_lte(stream, limit=5)
    assert next(stream) == b"1"
    assert is_lte is False

    # The whole stream in 12B long. 2 next calls have been made.
    # Therefore 10 elemments remain which we check against the limit.
    is_lte, stream = bytecount_lte(stream, limit=10)
    assert is_lte is True


def testbytecount_lte_with_empty_stream():
    """Test the behaviour if an empty stream is given."""
    original_data = b""
    stream = data_generator(original_data)
    is_lte, stream = bytecount_lte(stream, limit=5)
    assert is_lte is True


@pytest.mark.limit_memory("64 KB")
def test_bytecount_lte_memory_consumption():
    """Test that _bytecount_lte does not consume too much memory.

    This test is meant the unsure that the itertools.tee function does not keep the diff
    of both streams in memory. The test confirms that the diff of the streams is thrown
    away outside the _bytecount_lte function.
    """
    size = 1024**3  # 1 GiB
    stream = dummy_data_generator(size, 1024)
    is_lte, stream = bytecount_lte(stream, limit=1024)
    # Exhaust the stream to check if this has an influence on memory.
    for _ in stream:
        pass
    assert is_lte is False


def test_bytecount_lte_negative_limit_does_not_consume_stream():
    """Test that a negative limit is never satisfied and keeps the stream intact."""
    stream = data_generator(b"0123456789xx")

    is_lte, stream = bytecount_lte(stream, limit=-1)

    assert is_lte is False
    assert b"".join(stream) == b"0123456789xx"


@pytest.mark.limit_memory("8 MB")
def test_bytecount_lte_negative_limit_memory_consumption():
    """Test that a negative limit does not retain the stream via itertools.tee.

    A tee branch pins a whole block of already yielded chunks (CPython buffers 57 items
    per block), which for the mebibyte chunks the crawler streams meant tens of
    megabytes held for the lifetime of every download. A negative limit can never be
    satisfied, so there is nothing to tee in the first place.
    """
    size = 1024**3  # 1 GiB
    chunk_size = 1024**2  # 1 MiB
    is_lte, stream = bytecount_lte(dummy_data_generator(size, chunk_size), limit=-1)

    consumed = sum(len(chunk) for chunk in stream)

    assert is_lte is False
    assert consumed == size


def test_readable_stream_basic_read():
    """Test reading exact chunk sizes."""
    data = [b"abc", b"def", b"ghi"]
    stream = FileLikeStream(iter(data))

    assert stream.read(3) == b"abc"
    assert stream.read(3) == b"def"
    assert stream.read(3) == b"ghi"
    assert stream.read(3) == b""  # EOF


def test_readable_stream_buffering():
    """Test reading sizes smaller than the yielded chunks (buffering logic)."""
    data = [b"abcdefghi"]
    stream = FileLikeStream(iter(data))

    assert stream.read(3) == b"abc"
    assert stream.read(2) == b"de"
    assert stream.read(4) == b"fghi"
    assert stream.read(1) == b""


def test_readable_stream_never_spans_chunks():
    """Test that a read larger than the current chunk returns a short read.

    FileLikeStream is a raw stream, so read() may return fewer bytes than requested. It
    must never pull further chunks to satisfy the requested size, otherwise a consumer
    asking for a whole multipart part buffers that part here as well.
    """
    data = [b"a", b"b", b"c", b"d", b"e"]
    stream = FileLikeStream(iter(data))

    assert stream.read(3) == b"a"
    assert stream.read(10) == b"b"
    assert stream.read(10) == b"c"
    assert stream.read(10) == b"d"
    assert stream.read(10) == b"e"
    assert stream.read(10) == b""  # EOF


def test_readable_stream_read_all():
    """Test the -1 (read all) functionality."""
    data = [b"hello", b" ", b"world"]
    stream = FileLikeStream(iter(data))

    assert stream.read(-1) == b"hello world"
    assert stream.read(1) == b""


def test_readable_stream_mixed_logic():
    """Test a mix of large and small reads to ensure state persistence."""
    data = [b"1234567890", b"abcdefghij"]
    stream = FileLikeStream(iter(data))

    assert stream.read(5) == b"12345"  # Keeps "67890" of the current chunk
    assert stream.read(10) == b"67890"  # Rest of the current chunk, short read
    assert stream.read(-1) == b"abcdefghij"  # Returns remainder
    assert stream.read(-1) == b""  # Already empty


def test_readable_stream_empty_iterator():
    """Test behavior with an empty iterator."""
    stream = FileLikeStream(iter([]))
    assert stream.read(10) == b""
    assert stream.read(-1) == b""


def test_readable_stream_skips_empty_chunks():
    """Test that an empty chunk mid-stream is not reported as EOF.

    An empty read means EOF to every consumer, so an empty chunk yielded by the wrapped
    stream must be skipped rather than passed on.
    """
    data = [b"", b"abc", b"", b"", b"def", b""]
    stream = FileLikeStream(iter(data))

    assert stream.read(10) == b"abc"
    assert stream.read(10) == b"def"
    assert stream.read(10) == b""


def test_readable_stream_zero_size_read():
    """Test that a zero sized read does not consume the stream."""
    stream = FileLikeStream(iter([b"abc"]))

    assert stream.read(0) == b""
    assert stream.read(10) == b"abc"


def test_readable_stream_short_reads_reassemble_full_stream():
    """Test that a minio style consumer still receives the complete data.

    minio's read_part_data() loops over read() until the requested part is full, so
    short reads must not lose or reorder data.
    """
    data = [bytes([i]) * 1000 for i in range(20)]
    stream = FileLikeStream(iter(data))

    part_size = 4096
    parts = []
    while True:
        part = b""
        while len(part) < part_size:
            chunk = stream.read(part_size - len(part))
            if not chunk:
                break
            part += chunk
        if not part:
            break
        parts.append(part)

    assert b"".join(parts) == b"".join(data)


@pytest.mark.limit_memory("8 MB")
def test_readable_stream_memory_consumption():
    """Test that FileLikeStream does not materialise the stream for large reads.

    A consumer asking for a 10 MiB multipart part used to make FileLikeStream buffer
    that whole part (plus two copies of it) before returning. Streaming a gibibyte in
    mebibyte chunks must stay within a few chunks worth of memory.
    """
    size = 1024**3  # 1 GiB
    chunk_size = 1024**2  # 1 MiB
    part_size = 10 * 1024**2  # 10 MiB, the minio part size
    stream = FileLikeStream(dummy_data_generator(size, chunk_size))

    consumed = 0
    while data := stream.read(part_size + 1):
        consumed += len(data)

    assert consumed == size
