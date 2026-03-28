import hashlib
from typing import get_args

import pytest

from common.utils.iterhash import CountingHash, HashAlgorithm, iterhash

ALL_ALGORITHMS = get_args(HashAlgorithm)


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_counting_hash_basic(algorithm: HashAlgorithm) -> None:
    data = b"hello world"
    counting_hash = CountingHash(algorithm)
    counting_hash.update(data)

    expected_digest = hashlib.new(algorithm, data).hexdigest()
    assert counting_hash.hexdigest() == expected_digest
    assert counting_hash.bytes_count == len(data)


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_counting_hash_multiple_updates(algorithm: HashAlgorithm) -> None:
    chunks = [b"hello", b" ", b"world"]
    counting_hash = CountingHash(algorithm)

    for chunk in chunks:
        counting_hash.update(chunk)

    combined_data = b"".join(chunks)
    expected_digest = hashlib.new(algorithm, combined_data).hexdigest()
    assert counting_hash.hexdigest() == expected_digest
    assert counting_hash.bytes_count == len(combined_data)


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_counting_hash_empty(algorithm: HashAlgorithm) -> None:
    counting_hash = CountingHash(algorithm)

    assert counting_hash.bytes_count == 0
    assert counting_hash.hexdigest() == hashlib.new(algorithm, b"").hexdigest()


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_iterhash_yields_chunks(algorithm: HashAlgorithm) -> None:
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    counting_hash = CountingHash(algorithm)

    result = list(iterhash(counting_hash, iter(chunks)))

    assert result == chunks


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_iterhash_updates_hash(algorithm: HashAlgorithm) -> None:
    chunks = [b"hello", b" ", b"world"]
    counting_hash = CountingHash(algorithm)

    list(iterhash(counting_hash, iter(chunks)))

    combined_data = b"".join(chunks)
    expected_digest = hashlib.new(algorithm, combined_data).hexdigest()
    assert counting_hash.hexdigest() == expected_digest
    assert counting_hash.bytes_count == len(combined_data)


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_iterhash_empty_iterator(algorithm: HashAlgorithm) -> None:
    counting_hash = CountingHash(algorithm)
    initial_digest = counting_hash.hexdigest()

    result = list(iterhash(counting_hash, iter([])))

    assert not result
    assert counting_hash.hexdigest() == initial_digest
    assert counting_hash.bytes_count == 0
