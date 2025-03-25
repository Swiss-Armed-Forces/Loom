import logging
from typing import Any, Generator, Optional

from gridfs import GridFSBucket
from pymongo.client_session import ClientSession

from common.utils.gridfs import chunked_iterator_for_stream

logger = logging.getLogger(__name__)


class FileStorageService(GridFSBucket):
    """Service to store and retrieve files."""

    def open_download_iterator(
        self, file_id: Any, session: Optional[ClientSession] = None
    ) -> Generator[bytes, None, None]:
        with self.open_download_stream(file_id, session) as stream:
            yield from chunked_iterator_for_stream(stream)

    def open_download_iterator_by_name(
        self, filename: str, revision: int = -1, session: Optional[ClientSession] = None
    ) -> Generator[bytes, None, None]:
        with self.open_download_stream_by_name(filename, revision, session) as stream:
            yield from chunked_iterator_for_stream(stream)
