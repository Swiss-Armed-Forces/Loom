import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

from common.services.lazybytes_service import FileStorageLazyBytesService
from common.services.task_scheduling_service import (
    ArchiveImportRequest,
    TaskSchedulingService,
)
from common.utils.retry import retry
from minio import Minio

from crawler.archive_prescreen import IntakeObjectKind, classify_intake_object
from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_OBJECT_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 1 * 1024 * 1024
S3_RETRY_MAX_ATTEMPTS: int = 5
S3_RETRY_WAIT_S: int = 10
S3_MAX_CONCURRENT_DOWNLOADS: int = 4


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
        self._executor = ThreadPoolExecutor(max_workers=S3_MAX_CONCURRENT_DOWNLOADS)

    def _download_object(self, object_name: str, size: int):
        logger.info("Downloading object %s", object_name)
        full_name = Path(f"//{self.display_name}/{object_name}")
        source = f"{settings.crawler_source_id}/{self.bucket_name}"

        # Classified before the body is fetched. The crawler is the only part of
        # Loom holding an S3 client pointed at the object, which is what makes
        # an exact answer cost a few range reads here and a full extra
        # download-to-disk anywhere else -- see archive_prescreen.
        kind = classify_intake_object(self.client, self.bucket_name, object_name, size)

        def stream_generator():
            yield from self.client.get_object(self.bucket_name, object_name).stream(
                S3_READ_CHUNK_SIZE
            )

        uploaded_at = datetime.now()
        file_content = retry(
            lambda: self.file_storage_service.from_generator(stream_generator())
        )

        if kind is IntakeObjectKind.PLAIN_FILE:
            self.task_scheduling_service.dispatch_index_file(
                full_name=str(full_name),
                file_content=file_content,
                source_id=source,
                parent_id=None,
                uploaded_datetime=uploaded_at,
            )
            return

        logger.info("Object %s is a %s; importing it as an archive", object_name, kind)
        self.task_scheduling_service.dispatch_index_archive(
            ArchiveImportRequest(
                file_content=file_content,
                full_name=str(full_name),
                source_id=source,
                uploaded_datetime=uploaded_at,
            )
        )

    def crawl(self):
        logger.info(
            "Starting crawler for bucket '%s' (display name: '%s'), poll interval: %ds",
            self.bucket_name,
            self.display_name,
            S3_OBJECT_POLL_INTERVAL_S,
        )
        logger.info("Entering poll loop")
        while True:
            logger.debug("Polling bucket '%s' for objects", self.bucket_name)
            raw = retry(
                lambda: list(self.client.list_objects(self.bucket_name, recursive=True))
            )
            objects = sorted(
                raw,
                key=lambda o: o.last_modified
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            future_to_object = {}
            for obj in objects:
                if (
                    not obj.object_name
                    or not obj.last_modified
                    or _ProcessedObject(obj.object_name, obj.last_modified)
                    in self.processed_objects
                ):
                    continue

                logger.info("New object detected via polling: %s", obj.object_name)
                processed_object = _ProcessedObject(obj.object_name, obj.last_modified)
                future_to_object[
                    self._executor.submit(
                        self._download_object, obj.object_name, obj.size or 0
                    )
                ] = processed_object

            for future, processed_object in future_to_object.items():
                if exc := future.exception():
                    logger.error("Failed to download object: %s", exc)
                else:
                    self.processed_objects.add(processed_object)

            sleep(S3_OBJECT_POLL_INTERVAL_S)
