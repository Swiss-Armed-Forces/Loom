import logging
import time
from pathlib import Path
from threading import Thread

from common.dependencies import get_file_scheduling_service, get_lazybytes_service
from minio import Minio
from minio.datatypes import Bucket

from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_BUCKET_CHECK_INTERVAL_S: int = 300
S3_FILE_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 64 * 1024


class S3Crawler:
    def __init__(self, s3_client: Minio, buckets: list[str]):
        self.client = s3_client
        self.buckets = buckets
        self.bucket_crawlers: dict[Bucket, Thread] = {
            Bucket(bucket, None): Thread(target=None) for bucket in buckets
        }

    def _create_all_buckets(self):
        for bucket_name in self.buckets:
            if not self.client.bucket_exists(bucket_name):
                logger.info("Creating bucket: %s", bucket_name)
                self.client.make_bucket(bucket_name)

    def _recreate_crawlers(self):
        for bucket, crawler in self.bucket_crawlers.items():
            if not crawler.is_alive():
                self._create_bucket_crawler_thread(bucket)

    def _create_bucket_crawler_thread(self, bucket: Bucket):
        bucket_crawler_thread = _BucketCrawlerThread(self.client, bucket)
        bucket_crawler_thread.start()
        self.bucket_crawlers[bucket] = bucket_crawler_thread

    def crawl(self):
        self._create_all_buckets()
        while True:
            self._recreate_crawlers()
            time.sleep(S3_BUCKET_CHECK_INTERVAL_S)


class _BucketCrawlerThread(Thread):

    def __init__(self, client: Minio, bucket: Bucket):
        super().__init__()
        self.client = client
        self.bucket = bucket
        self.processed_files: set[str] = set()

    def run(self):
        self._poll_for_new_files()

    def _download_file(self, file_name: str):
        logger.info("Downloading file %s", file_name)
        self.processed_files.add(file_name)
        full_name = Path(f"//{self.bucket.name}/{file_name}")
        source = f"{settings.crawler_source_id}/{self.bucket}"

        def stream_generator():
            yield from self.client.get_object(self.bucket.name, file_name).stream(
                S3_READ_CHUNK_SIZE
            )

        file_content = get_lazybytes_service().from_generator(stream_generator())
        get_file_scheduling_service().index_file(
            full_name=str(full_name),
            file_content=file_content,
            source_id=source,
            parent_id=None,
        )

    def _poll_for_new_files(self):
        while True:
            files = self.client.list_objects(self.bucket.name, recursive=True)
            for file in files:
                if file.object_name and file.object_name not in self.processed_files:
                    logger.info("New file detected via polling: %s", file.object_name)
                    self._download_file(file.object_name)
            time.sleep(S3_FILE_POLL_INTERVAL_S)
