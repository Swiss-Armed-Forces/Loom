import pickle
import random
import time
from datetime import timedelta

import pytest
from common.dependencies import (
    get_file_storage_service,
    get_lazybytes_service,
)
from common.services.lazybytes_service import (
    LazyBytes,
    LazyBytesService,
)
from common.settings import settings
from pydantic import BaseModel


class SampleModel(BaseModel):
    """A Pydantic model for testing TypedLazyBytes."""

    value: int
    name: str


# pylint: disable=redefined-outer-name


@pytest.fixture
def large_data() -> bytes:
    return random.randbytes(settings.lazy_threshold_bytes * 3 + 1)


def data_generator(large_data: bytes):
    chunks = 30
    chunksize = max(1, len(large_data) // chunks)
    for i in range(0, len(large_data), chunksize):
        yield large_data[i : i + chunksize]


@pytest.fixture(params=["lazybytes", "filestorage"])
def lazy_bytes_service(request) -> LazyBytesService:
    match request.param:
        case "lazybytes":
            return get_lazybytes_service()
        case "filestorage":
            return get_file_storage_service()
        case _:
            raise AssertionError()


class TestLazyBytes:
    # pylint: disable=too-many-public-methods

    def test_load_memoryview(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_load_memoryview_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"asdfasdf")
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == b"asdfasdf"

    def test_load_file(self, lazy_bytes_service: LazyBytesService, large_data: bytes):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        with lazy_bytes_service.load_file(lazy_bytes) as tempfile:
            assert tempfile.read() == large_data

    def test_load_file_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"{}")
        with lazy_bytes_service.load_file(lazy_bytes) as tempfile:
            assert tempfile.read() == b"{}"

    def test_load_generator(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        lazy_generator = lazy_bytes_service.load_generator(lazy_bytes)
        assert b"".join(lazy_generator) == large_data

    def test_load_generator_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"generate meeee")
        lazy_generator = lazy_bytes_service.load_generator(lazy_bytes)
        assert next(lazy_generator) == b"generate meeee"

    def test_from_generator(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        lazy_bytes = lazy_bytes_service.from_generator(data_generator(large_data))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_from_generator_with_len(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
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

    def test_pickle(self, lazy_bytes_service: LazyBytesService, large_data: bytes):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data

    def test_pickle_small(self, lazy_bytes_service: LazyBytesService):
        lazy_bytes = lazy_bytes_service.from_bytes(b"asdfasdf")
        lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == b"asdfasdf"

    def test_from_object_pydantic_small(self, lazy_bytes_service: LazyBytesService):
        original = SampleModel(value=42, name="test")
        lazy = lazy_bytes_service.from_object(original)
        if len(pickle.dumps(original)) <= lazy_bytes_service.threshold_bytes:
            assert lazy.embedded_data is not None
        result = lazy_bytes_service.load_object(lazy)
        assert result == original

    def test_from_object_pydantic_large(self, lazy_bytes_service: LazyBytesService):
        original = list(range(settings.lazy_threshold_bytes))
        lazy = lazy_bytes_service.from_object(original)
        assert lazy.service_id is not None
        result = lazy_bytes_service.load_object(lazy)
        assert result == original

    def test_typed_lazy_bytes_pickle_roundtrip(
        self, lazy_bytes_service: LazyBytesService
    ):
        original = {"test": "data", "number": 123}
        lazy = lazy_bytes_service.from_object(original)
        lazy_restored = pickle.loads(pickle.dumps(lazy))
        result = lazy_bytes_service.load_object(lazy_restored)
        assert result == original

    def test_from_object_complex_nested(self, lazy_bytes_service: LazyBytesService):
        original = {
            "models": [SampleModel(value=1, name="a"), SampleModel(value=2, name="b")],
            "nested": {"deep": {"list": [1, 2, 3]}},
            "primitives": [1, "two", 3.0, None, True],
        }
        lazy = lazy_bytes_service.from_object(original)
        result = lazy_bytes_service.load_object(lazy)
        assert result == original

    def test_delete(self, lazy_bytes_service: LazyBytesService, large_data: bytes):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        # Verify data is accessible
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == large_data
        # Verify it was stored externally (not embedded)
        assert lazy_bytes.service_id is not None
        # Delete the data
        lazy_bytes_service.delete(lazy_bytes)

    def test_delete_small(self, lazy_bytes_service: LazyBytesService):
        small_data = b"small"

        # Skip if service never embeds data (e.g., filestorage with threshold=-1)
        if len(small_data) > lazy_bytes_service.threshold_bytes:
            pytest.skip(
                "Service never embeds data; embedding behavior tested elsewhere"
            )

        lazy_bytes = lazy_bytes_service.from_bytes(small_data)
        # Verify it's embedded (no service_id)
        assert lazy_bytes.service_id is None
        assert lazy_bytes.embedded_data is not None
        # Delete should be a no-op for embedded data
        lazy_bytes_service.delete(lazy_bytes)
        # Data should still be accessible
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert memory == small_data

    def test_delete_then_load_fails(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        assert lazy_bytes.service_id is not None
        lazy_bytes_service.delete(lazy_bytes)
        # Attempting to load deleted data should raise an exception
        with pytest.raises(Exception, match="."):
            with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
                _ = bytes(memory)  # Force load

    def test_flush_deletes_all(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        """Test that flush() with no args deletes all stored data."""
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        assert lazy_bytes.service_id is not None
        lazy_bytes_service.flush()
        # Data should be deleted
        with pytest.raises(Exception, match="."):
            with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
                _ = bytes(memory)

    def test_flush_with_min_age_preserves_recent(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        """Test that flush(min_age=...) preserves recently-created data."""
        # Store data and immediately flush with a min_age
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        assert lazy_bytes.service_id is not None
        # Flush only objects older than 5 minutes - our data is brand new
        lazy_bytes_service.flush(min_age=timedelta(seconds=10))
        # Data should still be accessible since it was just created
        with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
            assert bytes(memory) == large_data

    def test_flush_with_min_age_deletes_old(
        self, lazy_bytes_service: LazyBytesService, large_data: bytes
    ):
        """Test that flush(min_age=...) deletes data older than threshold."""
        # Store data
        lazy_bytes = lazy_bytes_service.from_bytes(large_data)
        assert lazy_bytes.service_id is not None
        # Wait for the data to age
        time.sleep(2)
        # Flush objects older than 1 second
        lazy_bytes_service.flush(min_age=timedelta(seconds=1))
        # Data should be deleted since it's older than 1 second
        with pytest.raises(Exception, match="."):
            with lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
                _ = bytes(memory)
