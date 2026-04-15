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


def test_readable_stream_multi_chunk_read():
    """Test reading sizes larger than a single yielded chunk."""
    data = [b"a", b"b", b"c", b"d", b"e"]
    stream = FileLikeStream(iter(data))

    # Needs to pull 3 chunks to satisfy this
    assert stream.read(3) == b"abc"
    # Needs to pull remaining 2 chunks
    assert stream.read(10) == b"de"


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

    assert stream.read(5) == b"12345"  # Buffers "67890"
    assert stream.read(10) == b"67890abcde"  # Uses buffer + pulls next chunk
    assert stream.read(-1) == b"fghij"  # Returns remainder
    assert stream.read(-1) == b""  # Already empty


def test_readable_stream_empty_iterator():
    """Test behavior with an empty iterator."""
    stream = FileLikeStream(iter([]))
    assert stream.read(10) == b""
    assert stream.read(-1) == b""
