import logging
import time
from pathlib import Path

from common.dependencies import get_file_scheduling_service, get_lazybytes_service
from minio import Minio

from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_FILE_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 64 * 1024


class S3Crawler:
    def __init__(self, s3_client: Minio, bucket_name: str, bucket_alias: str | None):
        self.client = s3_client
        self.bucket_name = bucket_name
        self.display_name = bucket_alias if bucket_alias else bucket_name
        self.processed_files: set[str] = set()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            logger.info("Creating bucket: %s", self.bucket_name)
            self.client.make_bucket(self.bucket_name)

    def _download_file(self, file_name: str):
        logger.info("Downloading file %s", file_name)
        self.processed_files.add(file_name)
        full_name = Path(f"//{self.display_name}/{file_name}")
        source = f"{settings.crawler_source_id}/{self.bucket_name}"

        def stream_generator():
            yield from self.client.get_object(self.bucket_name, file_name).stream(
                S3_READ_CHUNK_SIZE
            )

        file_content = get_lazybytes_service().from_generator(stream_generator())
        get_file_scheduling_service().index_file(
            full_name=str(full_name),
            file_content=file_content,
            source_id=source,
            parent_id=None,
        )

    def crawl(self):
        self._ensure_bucket()
        while True:
            files = self.client.list_objects(self.bucket_name, recursive=True)
            for file in files:
                if file.object_name and file.object_name not in self.processed_files:
                    logger.info("New file detected via polling: %s", file.object_name)
                    self._download_file(file.object_name)
            time.sleep(S3_FILE_POLL_INTERVAL_S)
