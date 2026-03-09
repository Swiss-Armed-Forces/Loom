import pickle
import random
from pathlib import Path

import pytest
from pydantic import BaseModel

from common.services.lazybytes_service import (
    InMemoryLazyBytesService,
    LazyBytes,
    TypedLazyBytes,
)
from common.settings import settings

# pylint: disable=redefined-outer-name


def random_large_data():
    return random.randbytes(settings.lazy_threshold_bytes * 3 + 1)


@pytest.fixture
def large_data():
    return random_large_data()


def data_generator(large_data):
    chunks = 30
    chunksize = max(1, len(large_data) // chunks)
    for i in range(0, len(large_data), chunksize):
        yield large_data[i : i + chunksize]


@pytest.fixture()
def in_memory_lazy_bytes_service():
    return InMemoryLazyBytesService()


def test_load_memoryview(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == large_data


def test_load_memoryview_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"asdfasdf")
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == b"asdfasdf"


def test_load_file(in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    with in_memory_lazy_bytes_service.load_file(lazy_bytes) as tempfile:
        assert tempfile.read() == large_data


def test_load_file_named(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    with in_memory_lazy_bytes_service.load_file_named(lazy_bytes) as tempfile:
        assert tempfile.read() == large_data


def test_load_file_named_has_name(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    prefix = "prefix"
    suffix = "suffix"
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    with in_memory_lazy_bytes_service.load_file_named(
        lazy_bytes=lazy_bytes, prefix=prefix, suffix=suffix
    ) as tempfile:
        tempfile_path = Path(tempfile.name)
        assert tempfile_path.is_relative_to(settings.tempfile_dir)
        assert tempfile_path.name.startswith(prefix)
        assert tempfile_path.name.endswith(suffix)


def test_load_file_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"{}")
    with in_memory_lazy_bytes_service.load_file(lazy_bytes) as tempfile:
        assert tempfile.read() == b"{}"


def test_load_file_named_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"{}")
    with in_memory_lazy_bytes_service.load_file_named(lazy_bytes) as tempfile:
        assert tempfile.read() == b"{}"


def test_load_file_named_small_has_name(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    prefix = "prefix"
    suffix = "suffix"
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"{}")
    with in_memory_lazy_bytes_service.load_file_named(
        lazy_bytes=lazy_bytes, prefix=prefix, suffix=suffix
    ) as tempfile:
        tempfile_path = Path(tempfile.name)
        assert tempfile_path.is_relative_to(settings.tempfile_dir)
        assert tempfile_path.name.startswith(prefix)
        assert tempfile_path.name.endswith(suffix)


def test_load_generator(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    with in_memory_lazy_bytes_service.load_generator(lazy_bytes) as lazy_generator:
        assert b"".join(lazy_generator) == large_data


def test_load_generator_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"generate meeee")
    with in_memory_lazy_bytes_service.load_generator(lazy_bytes) as lazy_generator:
        assert next(lazy_generator) == b"generate meeee"


def test_from_generator(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    lazy_bytes = in_memory_lazy_bytes_service.from_generator(data_generator(large_data))
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == large_data


def test_from_generator_with_len(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data
):
    lazy_bytes = in_memory_lazy_bytes_service.from_generator(
        data_generator(large_data), len(large_data)
    )
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == large_data


def test_from_generator_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    data = b"123xx"
    lazy_bytes = in_memory_lazy_bytes_service.from_generator(data_generator(data))
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == data


def test_from_generator_small_with_len(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    data = b"123xx"
    lazy_bytes = in_memory_lazy_bytes_service.from_generator(
        data_generator(data), len(data)
    )
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == data


def test_invalid_init_both_none():
    with pytest.raises(ValueError):
        LazyBytes(service_id=None, embedded_data=None)


def test_invalid_init_both_some():
    with pytest.raises(ValueError):
        LazyBytes(service_id=1234, embedded_data=b"asdf")


def test_valid_init_embedded():
    LazyBytes(service_id=None, embedded_data=b"asdf")


def test_valid_init_lazy():
    LazyBytes(service_id=1234, embedded_data=None)


def test_same_hash():
    assert hash(LazyBytes(service_id=1234, embedded_data=None)) == hash(
        LazyBytes(service_id=1234, embedded_data=None)
    )


def test_pickle(in_memory_lazy_bytes_service: InMemoryLazyBytesService, large_data):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(large_data)
    lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == large_data


def test_pickle_small(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    lazy_bytes = in_memory_lazy_bytes_service.from_bytes(b"asdfasdf")
    lazy_bytes = pickle.loads(pickle.dumps(lazy_bytes))
    with in_memory_lazy_bytes_service.load_memoryview(lazy_bytes) as memory:
        assert memory == b"asdfasdf"


# TypedLazyBytes tests


class SampleModel(BaseModel):
    """A Pydantic model for testing TypedLazyBytes with typed objects."""

    value: int
    name: str


def test_typed_lazy_bytes_inherits_lazy_bytes():
    """TypedLazyBytes should inherit from LazyBytes."""
    typed = TypedLazyBytes(embedded_data=b"test")
    assert isinstance(typed, LazyBytes)


def test_from_object_primitive_list(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """Test roundtrip of a primitive list."""
    original = [1, 2, 3, 4, 5]
    lazy = in_memory_lazy_bytes_service.from_object(original)
    result = in_memory_lazy_bytes_service.load_object(lazy)
    assert result == original


def test_from_object_dict(in_memory_lazy_bytes_service: InMemoryLazyBytesService):
    """Test roundtrip of a dictionary."""
    original = {"key": "value", "number": 42, "nested": {"a": 1}}
    lazy = in_memory_lazy_bytes_service.from_object(original)
    result = in_memory_lazy_bytes_service.load_object(lazy)
    assert result == original


def test_from_object_pydantic_model(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """Test roundtrip of a Pydantic model."""
    original = SampleModel(value=42, name="test")
    lazy = in_memory_lazy_bytes_service.from_object(original)
    result = in_memory_lazy_bytes_service.load_object(lazy)
    assert result == original


def test_from_object_small_embedded(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """Small objects should be embedded directly."""
    original = [1, 2, 3]
    lazy = in_memory_lazy_bytes_service.from_object(original)
    assert lazy.embedded_data is not None
    assert lazy.service_id is None


def test_from_object_large_stored(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """Large objects should be stored in the service."""
    # Create a large object that exceeds the threshold
    original = list(range(settings.lazy_threshold_bytes))
    lazy = in_memory_lazy_bytes_service.from_object(original)
    assert lazy.service_id is not None
    assert lazy.embedded_data is None
    # Verify roundtrip still works
    result = in_memory_lazy_bytes_service.load_object(lazy)
    assert result == original


def test_typed_lazy_bytes_can_be_pickled(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """TypedLazyBytes itself should be picklable (for Celery task arguments)."""
    original = {"test": "data"}
    lazy = in_memory_lazy_bytes_service.from_object(original)
    # Pickle and unpickle the TypedLazyBytes container
    lazy_restored = pickle.loads(pickle.dumps(lazy))
    # Should still be able to load the object
    result = in_memory_lazy_bytes_service.load_object(lazy_restored)
    assert result == original


def test_typed_lazy_bytes_large_can_be_pickled(
    in_memory_lazy_bytes_service: InMemoryLazyBytesService,
):
    """Large TypedLazyBytes (with service_id) should be picklable."""
    original = list(range(settings.lazy_threshold_bytes))
    lazy = in_memory_lazy_bytes_service.from_object(original)
    assert lazy.service_id is not None
    # Pickle and unpickle the TypedLazyBytes container
    lazy_restored = pickle.loads(pickle.dumps(lazy))
    # Should still be able to load the object
    result = in_memory_lazy_bytes_service.load_object(lazy_restored)
    assert result == original
