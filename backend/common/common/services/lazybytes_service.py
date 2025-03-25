from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timedelta
from io import SEEK_END, BytesIO
from mmap import PROT_READ, mmap
from tempfile import SpooledTemporaryFile, TemporaryFile
from typing import IO, Any, BinaryIO, Generator

from gridfs import GridFSBucket
from pydantic import BaseModel, ConfigDict, model_validator
from pymongo.database import Database

from common.settings import settings
from common.utils.gridfs import chunked_iterator_for_stream

LAZY_THRESHOLD_BYTES = 1024  # 1KiB


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


class LazyBytesService(ABC):
    def __init__(self):
        self.tempfile_dir = settings.tempfile_dir
        if self.tempfile_dir:
            self.tempfile_dir.mkdir(parents=True, exist_ok=True)

    def from_bytes(self, data: bytes) -> LazyBytes:
        """Stores the given data in this service."""
        if len(data) <= LAZY_THRESHOLD_BYTES:
            return LazyBytes(embedded_data=data)
        service_id = self._store(BytesIO(data))
        return LazyBytes(service_id=service_id)

    def from_generator(
        self, data: Generator[bytes, None, None], data_len: int | None = None
    ) -> LazyBytes:
        """Stores the given data in this service."""
        if data_len is not None and data_len <= LAZY_THRESHOLD_BYTES:
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

    def from_file(self, fd: BinaryIO | IO[bytes]) -> LazyBytes:
        """Stores the given data in this service."""
        # get filesize without calling .fileno()
        # -> calling .fileno will have the effect that
        #    python's SpooledTemporaryFiles are written to disk
        curr = fd.tell()
        fd.seek(0, SEEK_END)
        fd_size = fd.tell()
        fd.seek(0, curr)
        if fd_size <= LAZY_THRESHOLD_BYTES:
            return LazyBytes(embedded_data=fd.read())
        service_id = self._store(fd)
        return LazyBytes(service_id=service_id)

    @abstractmethod
    def _store(self, data: IO) -> Any:
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

    @contextmanager
    def load_generator(
        self, lazy_bytes: LazyBytes
    ) -> Generator[Generator[bytes, None, None], None, None]:
        # pylint: disable=protected-access
        if lazy_bytes.embedded_data is not None:

            def _embedded_data_generator():
                yield lazy_bytes.embedded_data

            yield _embedded_data_generator()
        else:
            yield self._load_to_generator(lazy_bytes.service_id)

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
            max_size=LAZY_THRESHOLD_BYTES, dir=self.tempfile_dir
        ) as dst:
            if lazy_bytes.embedded_data is not None:
                dst.write(lazy_bytes.embedded_data)
            else:
                self._load_to(lazy_bytes.service_id, dst)
            dst.flush()
            dst.seek(0)
            yield dst


class GridFSLazyBytesService(LazyBytesService):
    def __init__(self, database: Database):
        super().__init__()
        self._bucket = GridFSBucket(database)

    def _store(self, data: IO) -> Any:
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
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        query = {"uploadDate": {"$lt": one_minute_ago}}
        files_to_delete = self._bucket.find(query)
        for file in files_to_delete:
            self._bucket.delete(file._id)  # pylint: disable=protected-access


class InMemoryLazyBytesService(LazyBytesService):
    """All in-memory lazybytes service for testing.

    **!!DO NOT USE THIS IN PRODUCTION!!**.
    """

    def __init__(self):
        super().__init__()
        self._storage = []

    def _store(self, data: IO) -> Any:
        service_id = len(self._storage)
        self._storage.append(data.read())
        return service_id

    def _load_to(self, service_id: Any, dst: IO):
        dst.write(self._storage[service_id])

    def _load_to_generator(self, service_id: Any) -> Generator[bytes, None, None]:
        yield self._storage[service_id]

    def flush(self):
        self._storage = []
