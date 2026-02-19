import logging
import time
from pathlib import Path
from threading import Thread

from common.dependencies import get_file_scheduling_service, get_lazybytes_service
from minio import Minio
from minio.datatypes import Bucket

from crawler.settings import settings

logger = logging.getLogger(__name__)

MINIO_BUCKET_CHECK_INTERVAL_S: int = 300
MINIO_READ_CHUNK_SIZE: int = 64 * 1024


class MinioCrawler:
    def __init__(self, minio_client: Minio):
        self.client = minio_client
        self.bucket_crawlers: dict[Bucket, Thread] = {}

    def _reap_dead_bucket_crawlers(self):
        # Collect buckets to remove first
        buckets_to_remove = []
        for bucket, crawler in self.bucket_crawlers.items():
            if not crawler.is_alive():
                logger.info("Reaping crawler for bucket: %s", bucket)
                buckets_to_remove.append(bucket)

        # Then remove them
        for bucket in buckets_to_remove:
            del self.bucket_crawlers[bucket]

    def _create_bucket_crawler_for_new_buckets(self):
        for bucket in self.client.list_buckets():
            if bucket not in self.bucket_crawlers:
                logger.info("New bucket detected: %s", bucket)
                self._create_bucket_crawler_thread(bucket)

    def _create_bucket_crawler_thread(self, bucket: Bucket):
        bucket_crawler_thread = _BucketCrawlerThread(self.client, bucket)
        bucket_crawler_thread.start()
        self.bucket_crawlers[bucket] = bucket_crawler_thread

    def crawl(self):
        while True:
            self._reap_dead_bucket_crawlers()
            self._create_bucket_crawler_for_new_buckets()
            time.sleep(MINIO_BUCKET_CHECK_INTERVAL_S)


class _BucketCrawlerThread(Thread):

    def __init__(self, client: Minio, bucket: Bucket):
        super().__init__()
        self.client = client
        self.bucket = bucket

    def run(self):
        self._download_all_files()
        self._listen_for_bucket_notification()

    def _download_file(self, file_name: str):
        logger.info("Crawler downloading file %s", file_name)
        full_name = Path(f"//{self.bucket.name}/{file_name}")
        source = f"{settings.crawler_source_id}/{self.bucket.name}"
        get_file_scheduling_service().index_file(
            full_name=str(full_name),
            file_content=get_lazybytes_service().from_generator(
                self.client.get_object(self.bucket.name, file_name).stream(
                    MINIO_READ_CHUNK_SIZE
                )  # type: ignore
            ),
            source_id=source,
            parent_id=None,
        )

    def _download_all_files(self):
        files = self.client.list_objects(self.bucket.name, recursive=True)
        for file in files:
            if file.object_name is not None:
                self._download_file(file.object_name)

    def _listen_for_bucket_notification(self):
        with self.client.listen_bucket_notification(
            self.bucket.name,
            prefix="",
            events=["s3:ObjectCreated:*"],  # type: ignore
        ) as events:
            for event in events:
                for record in event.get("Records", []):
                    file_name = record["s3"]["object"]["key"]
                    self._download_file(file_name)
