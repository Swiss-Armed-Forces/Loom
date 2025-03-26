import logging
import time
from pathlib import Path
from threading import Thread

from common.dependencies import get_file_scheduling_service, get_lazybytes_service
from minio import Minio

from crawler.settings import settings

logger = logging.getLogger(__name__)

MINIO_BUCKET_CHECK_INTERVAL_S: int = 300
MINIO_READ_CHUNK_SIZE: int = 64 * 1024


class MinioCrawler:
    def __init__(self, minio_client: Minio):
        self.client = minio_client

        self.buckets: set[str] = set()
        self.collect_all_buckets()

    def crawl(self):
        while True:
            buckets = self.client.list_buckets()
            for bucket in buckets:
                if bucket.name not in self.buckets:
                    logger.info("New bucket detected %s", bucket.name)
                    self.buckets.add(bucket.name)
                    self.download_all_files(bucket.name)
                    self.create_bucket_notification_thread(bucket.name)

            time.sleep(MINIO_BUCKET_CHECK_INTERVAL_S)

    def collect_all_buckets(self):
        buckets = self.client.list_buckets()
        for bucket in buckets:
            self.buckets.add(bucket.name)
            self.download_all_files(bucket.name)
            self.create_bucket_notification_thread(bucket.name)

    def download_file(self, bucket_name: str, file_name: str):
        logger.info("Crawler detected file %s", file_name)
        full_name = Path(f"/{bucket_name}/{file_name}")
        source = f"{settings.crawler_source_id}/{bucket_name}"
        get_file_scheduling_service().index_file(
            str(full_name),
            get_lazybytes_service().from_generator(
                self.client.get_object(bucket_name, file_name).stream(
                    MINIO_READ_CHUNK_SIZE
                )  # type: ignore
            ),
            source,
        )

    def download_all_files(self, bucket_name: str):
        files = self.client.list_objects(bucket_name, recursive=True)
        for file in files:
            if file.object_name is not None:
                self.download_file(bucket_name, file.object_name)

    def create_bucket_notification_thread(self, bucket_name: str):
        notification_thread = Thread(
            target=_listen_for_notification, args=(self, bucket_name), daemon=True
        )

        notification_thread.start()


def _listen_for_notification(minio_crawler: MinioCrawler, bucket_name: str):
    with minio_crawler.client.listen_bucket_notification(
        bucket_name,
        prefix="",
        events=["s3:ObjectCreated:*"],  # type: ignore
    ) as events:
        for event in events:
            for record in event.get("Records", []):
                file_name = record["s3"]["object"]["key"]
                minio_crawler.download_file(bucket_name, file_name)
