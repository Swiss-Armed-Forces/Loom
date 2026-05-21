import logging
import pickle
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from io import SEEK_END, BytesIO
from mmap import PROT_READ, mmap
from tempfile import (
    NamedTemporaryFile,
    SpooledTemporaryFile,
    TemporaryFile,
    _TemporaryFileWrapper,
)
from typing import IO, Any, Generator, Generic, TypeVar, cast

from minio import Minio
from pydantic import BaseModel, ConfigDict, model_validator

from common.settings import settings
from common.utils.flush_s3_bucket import flush_s3_bucket
from common.utils.generator import FileLikeStream, bytecount_lte

logger = logging.getLogger(__name__)

S3_PART_SIZE = 10 * 1024 * 1024

T = TypeVar("T")
_Tag = TypeVar("_Tag")


class LazyBytes(BaseModel, Generic[_Tag]):
    """Serializable container for lazy-loadable byte data.

    The _Tag type parameter is a phantom type indicating which LazyBytesService instance
    this data belongs to (e.g. FileStorageTag or TempStorageTag). It carries no runtime
    information — it exists only for static type checking.
    """

    model_config = ConfigDict(frozen=True)

    service_id: Any | None = None
    embedded_data: bytes | None = None

    @model_validator(mode="after")
    def check_either_service_id_or_embedded_data(self) -> "LazyBytes[_Tag]":
        if self.service_id is None and self.embedded_data is None:
            msg = "no service id but no embedded data"
            raise ValueError(msg)
        if not (self.service_id is None or self.embedded_data is None):
            msg = "service id provided together with embedded data"
            raise ValueError(msg)
        return self

    def __reduce__(self):
        return (_rebuild_lazy_bytes, (self.model_dump(),))


def _rebuild_lazy_bytes(data: dict) -> "LazyBytes[Any]":
    """Reconstruct a LazyBytes instance during unpickling.

    Mirrors the TypedLazyBytes pattern: always reconstructs as the base
    (unparameterized) LazyBytes so pickle can find the class by qualified name.
    """
    return LazyBytes.model_validate(data)


class TypedLazyBytes(LazyBytes[_Tag], Generic[T, _Tag]):
    """Serializable container for typed lazy-loadable objects.

    T: the deserialized object type.
    _Tag: phantom service tag indicating which LazyBytesService produced this.

    Uses pickle for serialization, preserving type information.

    Note: __reduce__ reconstructs as unparameterized TypedLazyBytes[Any, Any],
    so both T and _Tag are lost after pickle/unpickle (same limitation as before
    for T). This is a known Pydantic v2 constraint — see _rebuild_typed_lazy_bytes.
    """

    def __reduce__(self):
        return (_rebuild_typed_lazy_bytes, (self.model_dump(),))


def _rebuild_typed_lazy_bytes(data: dict) -> "TypedLazyBytes":
    """Reconstruct a TypedLazyBytes instance during unpickling.

    This function exists to work around a known Pydantic v2 limitation: when a
    generic model (e.g. TypedLazyBytes[TikaResult]) is used as a field type in
    another Pydantic model, Pydantic creates a concrete parameterized subclass at
    runtime (e.g. TypedLazyBytes[TikaResult]). That subclass is not a module-level
    attribute, so pickle cannot find it by qualified name and raises PicklingError.

    By defining __reduce__ on TypedLazyBytes to point here, pickle always
    reconstructs instances using the base (unparameterized) TypedLazyBytes class,
    which IS importable.

    References:
    - https://github.com/pydantic/pydantic/issues/8913 (closed as not planned)
    - https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation
    """
    return TypedLazyBytes.model_validate(data)


class LazyBytesService(ABC, Generic[_Tag]):
    def __init__(self, *, threshold_bytes: int):
        self._threshold_bytes = threshold_bytes
        self.tempfile_dir = settings.tempfile_dir
        if self.tempfile_dir:
            self.tempfile_dir.mkdir(parents=True, exist_ok=True)

    @property
    def threshold_bytes(self) -> int:
        return self._threshold_bytes

    def from_bytes(self, data: bytes) -> "LazyBytes[_Tag]":
        """Stores the given data in this service."""
        if len(data) <= self._threshold_bytes:
            return cast("LazyBytes[_Tag]", LazyBytes(embedded_data=data))
        service_id = self._store(BytesIO(data))
        return cast("LazyBytes[_Tag]", LazyBytes(service_id=service_id))

    def from_generator(self, data: Iterator[bytes]) -> "LazyBytes[_Tag]":
        """Stores the given data in this service."""
        is_small, data = bytecount_lte(data, limit=self.threshold_bytes)
        if is_small:
            return cast("LazyBytes[_Tag]", LazyBytes(embedded_data=b"".join(data)))
        service_id = self._store(data)
        return cast("LazyBytes[_Tag]", LazyBytes(service_id=service_id))

    def from_file(self, fd: IO[bytes]) -> "LazyBytes[_Tag]":
        """Stores the given data in this service."""
        # get filesize without calling .fileno()
        # -> calling .fileno will have the effect that
        #    python's SpooledTemporaryFiles are written to disk
        curr = fd.tell()
        fd.seek(0, SEEK_END)
        fd_size = fd.tell()
        fd.seek(0, curr)
        if fd_size <= self._threshold_bytes:
            return cast("LazyBytes[_Tag]", LazyBytes(embedded_data=fd.read()))
        service_id = self._store(fd)
        return cast("LazyBytes[_Tag]", LazyBytes(service_id=service_id))

    def from_object(self, obj: T) -> "TypedLazyBytes[T, _Tag]":
        """Serializes an object using pickle and stores it as TypedLazyBytes.

        Args:
            obj: The object to serialize. Can be any picklable Python object.

        Returns:
            A TypedLazyBytes container for deserialization via load_object().
        """
        data = pickle.dumps(obj)
        if len(data) <= self._threshold_bytes:
            return cast("TypedLazyBytes[T, _Tag]", TypedLazyBytes(embedded_data=data))
        service_id = self._store(BytesIO(data))
        return cast("TypedLazyBytes[T, _Tag]", TypedLazyBytes(service_id=service_id))

    def delete(self, lazy_bytes: "LazyBytes[_Tag]"):
        """Deletes the data if stored in the service."""
        if lazy_bytes.service_id is None:
            return
        self._delete(lazy_bytes.service_id)

    @abstractmethod
    def _delete(self, service_id: Any):
        """Deletes the data in the service."""

    @abstractmethod
    def _store(self, data: Iterator[bytes] | IO[bytes]) -> Any:
        """Stores the data in the service returning a service id."""

    @abstractmethod
    def flush(self, min_age: timedelta | None = None):
        """Flush the data in the service.

        Args:
            min_age: Only delete objects older than this. If None, delete all.
        """

    @abstractmethod
    def get_total_size_bytes(self) -> int:
        """Get total size of all stored lazybytes in bytes."""

    @abstractmethod
    def _load_to(self, service_id: Any, dst: IO):
        """Loads the data at the given service id to dst."""

    @abstractmethod
    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        """Loads the data to the generator."""

    @contextmanager
    def _load_mmap(self, service_id: Any) -> Generator[mmap, None, None]:
        with TemporaryFile(dir=self.tempfile_dir) as dst:
            self._load_to(service_id, dst)
            # we flush here, because we have no guarantee that
            # the override of load_to called it.
            dst.flush()
            with mmap(dst.fileno(), 0, prot=PROT_READ) as mmap_memory:
                yield mmap_memory

    # Pylint contextmanager cleanup is a false positive
    # ref: https://github.com/pylint-dev/pylint/issues/9625
    @contextmanager
    def load_memoryview(  # pylint: disable=contextmanager-generator-missing-cleanup
        self, lazy_bytes: "LazyBytes[_Tag]"
    ) -> Generator[memoryview, None, None]:
        # pylint: disable=protected-access
        def yield_release(
            memview: memoryview,
        ) -> Generator[memoryview, None, None]:
            try:
                yield memview
            finally:
                memview.release()

        if lazy_bytes.embedded_data is not None:
            # using a loop here because of a pylint bug
            # ref: https://github.com/pylint-dev/pylint/issues/9252
            for x in yield_release(  # pylint: disable=use-yield-from
                memoryview(lazy_bytes.embedded_data)
            ):
                yield x
            # better:
            # yield from yield_release(memoryview(lazy_bytes.embedded_data))

        else:
            with self._load_mmap(lazy_bytes.service_id) as mmap_memory:
                # using a loop here because of a pylint bug
                # ref: https://github.com/pylint-dev/pylint/issues/9252
                for x in yield_release(  # pylint: disable=use-yield-from
                    memoryview(mmap_memory)
                ):
                    yield x
                # better:
                # yield from yield_release(memoryview(mmap_memory))

    def load_generator(
        self, lazy_bytes: "LazyBytes[_Tag]"
    ) -> Generator[bytes, None, None]:
        if lazy_bytes.embedded_data is not None:
            yield lazy_bytes.embedded_data
        else:
            yield from self._load_to_generator(lazy_bytes.service_id)

    @contextmanager
    def load_file(
        self, lazy_bytes: "LazyBytes[_Tag]"
    ) -> Generator[SpooledTemporaryFile[bytes], None, None]:
        # pylint: disable=protected-access
        #
        # Note do NOT use the following here:
        #
        # with self.load_memoryview(lazy_bytes) as memory:
        #     yield BytesIO(memory)
        #
        # I did quite a lot of experimentation and it looks that
        # BytesIO always copies the bytes given into an internal
        # buffer, even if it could just do copy on write.
        # There is this:
        # - https://bugs.python.org/issue22003
        # but I don't think that was every implemented and/or
        # can be used here.
        with SpooledTemporaryFile(
            max_size=self._threshold_bytes, dir=str(self.tempfile_dir)
        ) as dst:
            if lazy_bytes.embedded_data is not None:
                dst.write(lazy_bytes.embedded_data)
            else:
                self._load_to(lazy_bytes.service_id, dst)
            dst.flush()
            dst.seek(0)
            yield dst

    @contextmanager
    def load_file_named(
        self,
        lazy_bytes: "LazyBytes[_Tag]",
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> Generator[_TemporaryFileWrapper, None, None]:
        # pylint: disable=protected-access
        #
        # Note do NOT use the following here:
        #
        # with self.load_memoryview(lazy_bytes) as memory:
        #     yield BytesIO(memory)
        #
        # I did quite a lot of experimentation and it looks that
        # BytesIO always copies the bytes given into an internal
        # buffer, even if it could just do copy on write.
        # There is this:
        # - https://bugs.python.org/issue22003
        # but I don't think that was every implemented and/or
        # can be used here.
        with NamedTemporaryFile(
            prefix=prefix, suffix=suffix, dir=str(self.tempfile_dir)
        ) as dst:
            if lazy_bytes.embedded_data is not None:
                dst.write(lazy_bytes.embedded_data)
            else:
                self._load_to(lazy_bytes.service_id, dst)
            dst.flush()
            dst.seek(0)
            yield dst

    def load_object(self, lazy_bytes: "TypedLazyBytes[T, _Tag]") -> T:
        """Deserializes TypedLazyBytes back to an object.

        Args:
            lazy_bytes: The TypedLazyBytes container created by from_object().

        Returns:
            The deserialized object.
        """
        with self.load_memoryview(lazy_bytes) as memview:
            return pickle.loads(memview)


class S3LazyBytesService(LazyBytesService[_Tag]):
    def __init__(self, client: Minio, bucket: str, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._client = client
        self._bucket = bucket

    def _store(self, data: Iterator[bytes] | IO[bytes]) -> Any:
        id_ = uuid.uuid4()
        file_like = data
        if not hasattr(data, "read"):
            file_like = FileLikeStream(data)
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
        self._client.put_object(
            self._bucket,
            str(id_),
            # This function should be taking IO[bytes] instead of
            # BytesIO, as IO[bytes] is the parent class
            file_like,  # type: ignore
            length=-1,
            part_size=S3_PART_SIZE,
        )
        return id_

    def _load_to(self, service_id: Any, dst: IO):
        response = self._client.get_object(self._bucket, str(service_id))
        for chunk in response.stream():
            dst.write(chunk)

    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        response = self._client.get_object(self._bucket, str(service_id))
        yield from response.stream()

    def flush(self, min_age: timedelta | None = None):
        flush_s3_bucket(self._client, self._bucket, min_age=min_age)

    def _delete(self, service_id: Any):
        self._client.remove_object(self._bucket, str(service_id))

    def get_total_size_bytes(self) -> int:
        total = 0
        if not self._client.bucket_exists(self._bucket):
            return 0
        for obj in self._client.list_objects(self._bucket):
            if obj.size is not None:
                total += obj.size
        return total


class FileStorageTag:  # pylint: disable=too-few-public-methods
    """Phantom tag for LazyBytes stored in the permanent file storage service."""


class TempStorageTag:  # pylint: disable=too-few-public-methods
    """Phantom tag for LazyBytes stored in the ephemeral pipeline lazybytes service."""


# Convenience aliases — prefer these over bare LazyBytes/TypedLazyBytes[..., Tag]
FileStorageLazyBytes = LazyBytes[FileStorageTag]
TempLazyBytes = LazyBytes[TempStorageTag]

type FileStorageTypedLazyBytes[T] = TypedLazyBytes[T, FileStorageTag]
type TempTypedLazyBytes[T] = TypedLazyBytes[T, TempStorageTag]


class FileStorageLazyBytesService(S3LazyBytesService[FileStorageTag]):
    """S3-backed service for permanent file storage."""


class TempLazyBytesService(S3LazyBytesService[TempStorageTag]):
    """S3-backed service for ephemeral pipeline storage."""


class InMemoryLazyBytesService(LazyBytesService[_Tag]):
    """All in-memory lazybytes service for testing.

    **!!DO NOT USE THIS IN PRODUCTION!!**.
    """

    def __init__(self, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._storage: dict[int, bytes] = {}
        self._counter = 0

    def _store(self, data: Iterator[bytes] | IO[bytes]) -> Any:
        service_id = len(self._storage)
        self._storage[service_id] = b"".join(data)
        return service_id

    def _get_service_id(self) -> int:
        service_id = self._counter
        self._counter += 1
        return service_id

    def _load_to(self, service_id: Any, dst: IO):
        dst.write(self._storage[service_id])

    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        yield self._storage[service_id]

    def flush(self, min_age: timedelta | None = None):
        # InMemoryLazyBytesService doesn't track timestamps, so min_age is ignored
        del min_age  # unused
        self._storage = {}

    def _delete(self, service_id: Any):
        del self._storage[service_id]

    def get_total_size_bytes(self) -> int:
        return sum(len(data) for data in self._storage.values())


class InMemoryFileStorageLazyBytesService(InMemoryLazyBytesService[FileStorageTag]):
    """In-memory variant of FileStorageLazyBytesService.

    For testing only.
    """


class InMemoryTempLazyBytesService(InMemoryLazyBytesService[TempStorageTag]):
    """In-memory variant of TempLazyBytesService.

    For testing only.
    """
