import pickle
import random

import pytest
from common.dependencies import get_lazybytes_service
from common.services.lazybytes_service import (
    LAZY_THRESHOLD_BYTES,
    LazyBytes,
    LazyBytesService,
)

# pylint: disable=redefined-outer-name


def random_large_data():
    return random.randbytes(LAZY_THRESHOLD_BYTES * 3 + 1)


@pytest.fixture
def large_data():
    return random_large_data()


def data_generator(large_data):
    chunks = 30
    chunksize = max(1, len(large_data) // chunks)
    for i in range(0, len(large_data), chunksize):
        yield large_data[i : i + chunksize]


@pytest.fixture()
def lazy_bytes_service():
    return get_lazybytes_service()


class TestLazybytes:

    def test_load_memoryview(self, lazy_bytes_service: LazyBytesService, large_data):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_load_memoryview_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"asdfasdf")
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == b"asdfasdf"

    def test_load_file(self, lazy_bytes_service: LazyBytesService, large_data):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        with lazy_bytes_service.load_file(lazy_bytes) as tempfile:
            assert tempfile.read() == large_data

    def test_load_file_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"{}")
        with lazy_bytes_service.load_file(lazy_bytes) as tempfile:
            assert tempfile.read() == b"{}"

    def test_load_generator(self, lazy_bytes_service: LazyBytesService, large_data):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        with lazy_bytes_service.load_generator(lazy_bytes) as lazy_generator:
            assert b"".join(lazy_generator) == large_data

    def test_load_generator_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"generate meeee")
        with lazy_bytes_service.load_generator(lazy_bytes) as lazy_generator:
            assert next(lazy_generator) == b"generate meeee"

    def test_from_generator(self, lazy_bytes_service: LazyBytesService, large_data):
        lazy_bytes = lazy_bytes_service.from_generator(data_generator(large_data))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_from_generator_with_len(
        self, lazy_bytes_service: LazyBytesService, large_data
    ):
        lazy_bytes = lazy_bytes_service.from_generator(
            data_generator(large_data), len(large_data)
        )
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_from_generator_small(self, lazy_bytes_service: LazyBytesService):
        data = b"123xx"
        lazy_bytes = lazy_bytes_service.from_generator(data_generator(data))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == data

    def test_from_generator_small_with_len(
        self,
        lazy_bytes_service: LazyBytesService,
    ):
        data = b"123xx"
        lazy_bytes = lazy_bytes_service.from_generator(data_generator(data), len(data))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == data

    def test_invalid_init_both_none(
        self,
    ):
        with pytest.raises(ValueError):
            LazyBytes(service_id=None, embedded_data=None)

    def test_invalid_init_both_some(
        self,
    ):
        with pytest.raises(ValueError):
            LazyBytes(service_id=1234, embedded_data=b"asdf")

    def test_valid_init_embedded(
        self,
    ):
        LazyBytes(service_id=None, embedded_data=b"asdf")

    def test_valid_init_lazy(
        self,
    ):
        LazyBytes(service_id=1234, embedded_data=None)

    def test_same_hash(
        self,
    ):
        assert hash(LazyBytes(service_id=1234, embedded_data=None)) == hash(
            LazyBytes(service_id=1234, embedded_data=None)
        )

    def test_pickle(self, lazy_bytes_service: LazyBytesService, large_data):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_pickle_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"asdfasdf")
        lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == b"asdfasdf"
