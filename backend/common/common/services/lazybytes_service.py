import logging
import pickle
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from io import SEEK_END, BytesIO
from math import ceil
from mmap import PROT_READ, mmap
from tempfile import (
    NamedTemporaryFile,
    SpooledTemporaryFile,
    TemporaryFile,
    _TemporaryFileWrapper,
)
from typing import IO, Any, Generator, Generic, TypeVar

from gridfs import GridFSBucket
from minio import Minio
from pydantic import BaseModel, ConfigDict, model_validator
from pymongo.database import Database

from common.settings import settings
from common.utils.flush_s3_bucket import flush_s3_bucket
from common.utils.gridfs import chunked_iterator_for_stream

logger = logging.getLogger(__name__)

S3_PART_SIZE = 10 * 1024 * 1024

T = TypeVar("T")


class LazyBytes(BaseModel):
    """Serializable container for lazy-loadable byte data."""

    model_config = ConfigDict(frozen=True)

    service_id: Any | None = None
    embedded_data: bytes | None = None

    @model_validator(mode="after")
    def check_either_service_id_or_embedded_data(self) -> "LazyBytes":
        if self.service_id is None and self.embedded_data is None:
            msg = "no service id but no embedded data"
            raise ValueError(msg)
        if not (self.service_id is None or self.embedded_data is None):
            msg = "service id provided together with embedded data"
            raise ValueError(msg)
        return self


class TypedLazyBytes(LazyBytes, Generic[T]):
    """Serializable container for typed lazy-loadable objects.

    Uses pickle for serialization, preserving type information.
    """


class LazyBytesService(ABC):
    def __init__(self, *, threshold_bytes: int):
        self._threshold_bytes = threshold_bytes
        self.tempfile_dir = settings.tempfile_dir
        if self.tempfile_dir:
            self.tempfile_dir.mkdir(parents=True, exist_ok=True)

    @property
    def threshold_bytes(self) -> int:
        return self._threshold_bytes

    def from_bytes(self, data: bytes) -> LazyBytes:
        """Stores the given data in this service."""
        if len(data) <= self._threshold_bytes:
            return LazyBytes(embedded_data=data)
        service_id = self._store(BytesIO(data))
        return LazyBytes(service_id=service_id)

    def from_generator(
        self, data: Iterator[bytes], data_len: int | None = None
    ) -> LazyBytes:
        """Stores the given data in this service."""
        if data_len is not None and data_len <= self._threshold_bytes:
            return LazyBytes(
                embedded_data=bytes(int.from_bytes(b, byteorder="little") for b in data)
            )
        # buffer generator into temporary file
        with TemporaryFile(dir=self.tempfile_dir) as tmp:
            for i in data:
                tmp.write(i)
            tmp.flush()
            tmp.seek(0)
            return self.from_file(tmp)

    def from_file(self, fd: IO[bytes]) -> LazyBytes:
        """Stores the given data in this service."""
        # get filesize without calling .fileno()
        # -> calling .fileno will have the effect that
        #    python's SpooledTemporaryFiles are written to disk
        curr = fd.tell()
        fd.seek(0, SEEK_END)
        fd_size = fd.tell()
        fd.seek(0, curr)
        if fd_size <= self._threshold_bytes:
            return LazyBytes(embedded_data=fd.read())
        service_id = self._store(fd)
        return LazyBytes(service_id=service_id)

    def from_object(self, obj: T) -> TypedLazyBytes[T]:
        """Serializes an object using pickle and stores it as TypedLazyBytes.

        Args:
            obj: The object to serialize. Can be any picklable Python object.

        Returns:
            A TypedLazyBytes container for deserialization via load_object().
        """
        data = pickle.dumps(obj)
        if len(data) <= self._threshold_bytes:
            return TypedLazyBytes(embedded_data=data)
        service_id = self._store(BytesIO(data))
        return TypedLazyBytes(service_id=service_id)

    def delete(self, lazy_bytes: LazyBytes):
        """Deletes the data if stored in the service."""
        if lazy_bytes.service_id is None:
            return
        self._delete(lazy_bytes.service_id)

    @abstractmethod
    def _delete(self, service_id: Any):
        """Deletes the data in the service."""

    @abstractmethod
    def _store(self, data: IO[bytes]) -> Any:
        """Stores the data in the service returning a service id."""

    @abstractmethod
    def flush(self):
        """Flush the data in the service."""

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
        self, lazy_bytes: LazyBytes
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

    def load_generator(self, lazy_bytes: LazyBytes) -> Generator[bytes, None, None]:
        if lazy_bytes.embedded_data is not None:
            yield lazy_bytes.embedded_data
        else:
            yield from self._load_to_generator(lazy_bytes.service_id)

    @contextmanager
    def load_file(
        self, lazy_bytes: LazyBytes
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
        lazy_bytes: LazyBytes,
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

    def load_object(self, lazy_bytes: TypedLazyBytes[T]) -> T:
        """Deserializes TypedLazyBytes back to an object.

        Args:
            lazy_bytes: The TypedLazyBytes container created by from_object().

        Returns:
            The deserialized object.
        """
        with self.load_memoryview(lazy_bytes) as memview:
            return pickle.loads(memview)


class GridFSLazyBytesService(LazyBytesService):
    def __init__(self, database: Database, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._database = database
        self._bucket = GridFSBucket(database)

    def _store(self, data: IO[bytes]) -> Any:
        id_ = self._bucket.upload_from_stream(
            # We leave the filename empty in the upload because
            # this service is only concerned by the data itself.
            # Two writes to the same filename (in this case the
            # empty string) does not mean that data will be
            # overwritten in GridFS.
            "",
            data,
        )
        return id_

    def _load_to(self, service_id: Any, dst: IO):
        self._bucket.download_to_stream(service_id, dst)

    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        with self._bucket.open_download_stream(service_id) as stream:
            yield from chunked_iterator_for_stream(stream)

    def flush(self):
        # Deletes lazybytes assuming they are no longer used because it's only
        # only called once the system is idle.
        # To prevent deleting of incomplete uploads we check if the number of
        # chunks is what we expect.
        # If a file is older than one hour it is deleted regardless.
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        query = {"uploadDate": {"$lt": one_minute_ago}}
        files_to_delete = self._bucket.find(query)
        for file in files_to_delete:
            file_id = file._id  # pylint: disable=protected-access
            if file.length > file.chunk_size and file.upload_date > one_hour_ago:
                # file has many chunks and was recently uploaded, might still be uploading:
                expected_chunks = ceil(file.length / file.chunk_size)
                actual_chunks = self._database.fs.chunks.count_documents(
                    {"files_id": file_id}
                )

                if actual_chunks < expected_chunks:
                    # not all chunks uploaded yet: skip delete
                    logger.info("Not Flushing: %s", file_id)
                    continue
            logger.info("Flushing: %s", file_id)
            self._bucket.delete(file_id)
        # Compact Collections in Database
        logger.info("Compacting collections")
        self._database.command("compact", "fs.files")
        self._database.command("compact", "fs.chunks")

    def _delete(self, service_id: Any):
        self._bucket.delete(service_id)


class S3LazyBytesService(LazyBytesService):
    def __init__(self, client: Minio, bucket: str, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._client = client
        self._bucket = bucket

    def _store(self, data: IO[bytes]) -> Any:
        id_ = uuid.uuid4()
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
        self._client.put_object(
            self._bucket,
            str(id_),
            # This function should be taking IO[bytes] instead of
            # BytesIO, as IO[bytes] is the parent class
            data,  # type: ignore
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

    def flush(self):
        flush_s3_bucket(self._client, self._bucket)

    def _delete(self, service_id: Any):
        self._client.remove_object(self._bucket, str(service_id))


class InMemoryLazyBytesService(LazyBytesService):
    """All in-memory lazybytes service for testing.

    **!!DO NOT USE THIS IN PRODUCTION!!**.
    """

    def __init__(self, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._storage: dict[int, bytes] = {}
        self._counter = 0

    def _get_service_id(self) -> int:
        service_id = self._counter
        self._counter += 1
        return service_id

    def _store(self, data: IO[bytes]) -> Any:
        service_id = self._get_service_id()
        self._storage[service_id] = data.read()
        return service_id

    def _load_to(self, service_id: Any, dst: IO):
        dst.write(self._storage[service_id])

    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        yield self._storage[service_id]

    def flush(self):
        self._storage = {}

    def _delete(self, service_id: Any):
        del self._storage[service_id]
