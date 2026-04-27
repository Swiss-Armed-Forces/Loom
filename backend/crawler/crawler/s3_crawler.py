import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

from common.dependencies import get_file_scheduling_service
from common.services.lazybytes_service import LazyBytesService
from minio import Minio

from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_FILE_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 64 * 1024
S3_RETRY_MAX_ATTEMPTS: int = 5
S3_RETRY_WAIT_S: int = 10


_T = TypeVar("_T")


def _retry(
    fn: Callable[[], _T],
    max_attempts: int = S3_RETRY_MAX_ATTEMPTS,
    wait_s: int = S3_RETRY_WAIT_S,
) -> _T:
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            if attempt < max_attempts:
                logger.warning(
                    "Attempt %d/%d failed (%s). Retrying in %ds...",
                    attempt,
                    max_attempts,
                    exc,
                    wait_s,
                )
                time.sleep(wait_s)
            else:
                logger.error("All %d attempts failed: %s", max_attempts, exc)
                raise
    raise AssertionError("unreachable")


class S3Crawler:
    def __init__(
        self,
        s3_client: Minio,
        bucket_name: str,
        bucket_alias: str | None,
        lazybytes_service: LazyBytesService,
    ):
        self.client = s3_client
        self.bucket_name = bucket_name
        self.display_name = bucket_alias if bucket_alias else bucket_name
        self.lazybytes_service = lazybytes_service
        self.processed_files: set[str] = set()

    def _ensure_bucket(self):
        if not _retry(lambda: self.client.bucket_exists(self.bucket_name)):
            logger.info("Creating bucket: %s", self.bucket_name)
            _retry(lambda: self.client.make_bucket(self.bucket_name))

    def _download_file(self, file_name: str):
        logger.info("Downloading file %s", file_name)
        self.processed_files.add(file_name)
        full_name = Path(f"//{self.display_name}/{file_name}")
        source = f"{settings.crawler_source_id}/{self.bucket_name}"

        def stream_generator():
            yield from self.client.get_object(self.bucket_name, file_name).stream(
                S3_READ_CHUNK_SIZE
            )

        file_content = _retry(
            lambda: self.lazybytes_service.from_generator(stream_generator())
        )
        get_file_scheduling_service().index_file(
            full_name=str(full_name),
            file_content=file_content,
            source_id=source,
            parent_id=None,
        )

    def crawl(self):
        self._ensure_bucket()
        while True:
            raw = _retry(
                lambda: list(self.client.list_objects(self.bucket_name, recursive=True))
            )
            files = sorted(
                raw,
                key=lambda o: o.last_modified
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            for file in files:
                if file.object_name and file.object_name not in self.processed_files:
                    logger.info("New file detected via polling: %s", file.object_name)
                    self._download_file(file.object_name)
            time.sleep(S3_FILE_POLL_INTERVAL_S)
