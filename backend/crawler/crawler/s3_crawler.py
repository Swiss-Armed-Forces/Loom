import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

from common.services.lazybytes_service import FileStorageLazyBytesService
from common.services.task_scheduling_service import TaskSchedulingService
from common.utils.retry import retry
from minio import Minio

from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_OBJECT_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 64 * 1024
S3_RETRY_MAX_ATTEMPTS: int = 5
S3_RETRY_WAIT_S: int = 10


@dataclass(frozen=True)
class _ProcessedObject:
    object_name: str
    last_modified: datetime


class S3Crawler:
    def __init__(
        self,
        s3_client: Minio,
        bucket_name: str,
        bucket_alias: str | None,
        file_storage_service: FileStorageLazyBytesService,
        task_scheduling_service: TaskSchedulingService,
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self.client = s3_client
        self.bucket_name = bucket_name
        self.display_name = bucket_alias if bucket_alias else bucket_name
        self.file_storage_service = file_storage_service
        self.task_scheduling_service = task_scheduling_service
        self.processed_objects: set[_ProcessedObject] = set()

    def _ensure_bucket(self):
        if not retry(lambda: self.client.bucket_exists(self.bucket_name)):
            logger.info("Creating bucket: %s", self.bucket_name)
            retry(lambda: self.client.make_bucket(self.bucket_name))

    def _download_object(self, object_name: str, last_modified: datetime):
        logger.info("Downloading object %s", object_name)
        self.processed_objects.add(_ProcessedObject(object_name, last_modified))
        full_name = Path(f"//{self.display_name}/{object_name}")
        source = f"{settings.crawler_source_id}/{self.bucket_name}"

        def stream_generator():
            yield from self.client.get_object(self.bucket_name, object_name).stream(
                S3_READ_CHUNK_SIZE
            )

        uploaded_at = datetime.now()
        file_content = retry(
            lambda: self.file_storage_service.from_generator(stream_generator())
        )
        self.task_scheduling_service.dispatch_index_file(
            full_name=str(full_name),
            file_content=file_content,
            source_id=source,
            parent_id=None,
            uploaded_datetime=uploaded_at,
        )

    def crawl(self):
        self._ensure_bucket()
        while True:
            raw = retry(
                lambda: list(self.client.list_objects(self.bucket_name, recursive=True))
            )
            objects = sorted(
                raw,
                key=lambda o: o.last_modified
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            for obj in objects:
                if (
                    obj.object_name
                    and obj.last_modified
                    and _ProcessedObject(obj.object_name, obj.last_modified)
                    not in self.processed_objects
                ):
                    logger.info("New object detected via polling: %s", obj.object_name)
                    self._download_object(obj.object_name, obj.last_modified)
            sleep(S3_OBJECT_POLL_INTERVAL_S)
