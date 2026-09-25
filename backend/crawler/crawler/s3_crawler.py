import logging
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import sleep

from common.services.lazybytes_service import FileStorageLazyBytesService
from common.services.task_scheduling_service import (
    ArchiveImportRequest,
    TaskSchedulingService,
)
from common.utils.retry import retry
from minio import Minio
from minio.datatypes import Object

from crawler.archive_prescreen import IntakeObjectKind, classify_intake_object
from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_OBJECT_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 1 * 1024 * 1024
S3_RETRY_MAX_ATTEMPTS: int = 5
S3_RETRY_WAIT_S: int = 10
S3_MAX_CONCURRENT_DOWNLOADS: int = 4

# How far behind the newest object it has taken the crawler still remembers
# individual objects for.
#
# The record of what has been processed used to grow for the life of the pod, one
# entry per object ever seen. That was fine when this bucket received occasional
# manual uploads; it is not fine now that it is where a whole USB stick is mirrored
# (nixos/usb-ingest.nix defaults `--bucket loom-intake`, and nothing deletes from it
# afterwards), because three sticks in, the set is hundreds of thousands of entries
# that are never released.
#
# Anything older than this is taken as already done. That is safe because S3 stamps
# `last_modified` when the object is *written*: nothing puts an old timestamp on a
# new object, since `mc mirror` is run without `--preserve`. The window is therefore
# only covering clock skew between the gateway and this pod, and objects that became
# visible out of order -- both of which are seconds, not an hour.
WATERMARK_GRACE = timedelta(hours=1)


@dataclass(frozen=True)
class _ProcessedObject:
    object_name: str
    last_modified: datetime


class ProcessedLedger:
    """What has already been handled, and the watermark that bounds how much is kept.

    One object rather than a set and a datetime side by side on the crawler, because
    they are one rule: an object is done if it is remembered individually *or* if it
    is old enough that the watermark speaks for it, and the two only stay consistent
    if they move together.
    """

    def __init__(self) -> None:
        self._seen: set[_ProcessedObject] = set()
        # None until something has actually been processed, so a freshly started pod
        # never skips an object on the strength of a watermark it has not earned.
        self.watermark: datetime | None = None

    def __len__(self) -> int:
        return len(self._seen)

    @property
    def names(self) -> frozenset[str]:
        """The objects still remembered individually.

        For assertions and logging.
        """
        return frozenset(entry.object_name for entry in self._seen)

    def covers(self, object_name: str, last_modified: datetime) -> bool:
        """Whether this object has been handled already."""
        if self.watermark is not None and last_modified <= self.watermark:
            return True
        return _ProcessedObject(object_name, last_modified) in self._seen

    def record(self, obj: "IntakeObject") -> None:
        """Remember an object, until the watermark comes to cover it."""
        self._seen.add(_ProcessedObject(obj.object_name, obj.last_modified))

    def advance(self) -> None:
        """Move the watermark up and forget everything it now covers.

        The grace period is what makes this safe rather than merely cheap: the
        watermark trails the newest processed object, so an object written while a
        poll was in flight is still ahead of it. See `WATERMARK_GRACE`.
        """
        if not self._seen:
            return

        newest = max(entry.last_modified for entry in self._seen)
        watermark = newest - WATERMARK_GRACE
        if self.watermark is not None and watermark <= self.watermark:
            return

        self.watermark = watermark
        self._seen = {entry for entry in self._seen if entry.last_modified > watermark}


@dataclass(frozen=True)
class IntakeObject:
    """One listed object, with the three fields this loop actually uses.

    A declared shape rather than minio's `Object` so the filtering below can be reasoned
    about -- and tested -- without a client.
    """

    object_name: str
    last_modified: datetime
    size: int


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
        self.processed = ProcessedLedger()
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
            response = self.client.get_object(self.bucket_name, object_name)
            try:
                yield from response.stream(S3_READ_CHUNK_SIZE)
            finally:
                # minio requires both calls, otherwise the buffered response and its
                # connection stay alive - notably when retry() abandons a partially
                # consumed stream.
                response.close()
                response.release_conn()

        # Aware: this is indexed as an Elasticsearch Date and ordered on, and a naive
        # local timestamp sorts inconsistently against anything written with a zone.
        uploaded_at = datetime.now(timezone.utc)
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

            # Filtered before it is sorted, not after. The listing is the whole
            # bucket -- S3 has no way to ask for "objects newer than X", since
            # `start_after` is lexicographic by key and these keys are not in time
            # order -- so after a few sticks it is hundreds of thousands of entries,
            # and sorting all of them every five seconds was most of what this loop
            # did. What is new is a handful.
            fresh = self.unprocessed(raw)
            fresh.sort(key=lambda o: o.last_modified, reverse=True)

            future_to_object = {}
            for obj in fresh:
                logger.info("New object detected via polling: %s", obj.object_name)
                future_to_object[
                    self._executor.submit(
                        self._download_object, obj.object_name, obj.size
                    )
                ] = obj

            for future, processed_object in future_to_object.items():
                if exc := future.exception():
                    logger.error("Failed to download object: %s", exc)
                else:
                    self.processed.record(processed_object)

            self.processed.advance()
            sleep(S3_OBJECT_POLL_INTERVAL_S)

    def unprocessed(self, listing: Iterable[Object]) -> list[IntakeObject]:
        """The objects in a listing that still have to be handled."""
        fresh = []
        for obj in listing:
            name = obj.object_name
            last_modified = obj.last_modified
            if not name or not last_modified:
                continue
            if self.processed.covers(name, last_modified):
                continue
            fresh.append(
                IntakeObject(
                    object_name=name,
                    last_modified=last_modified,
                    size=obj.size or 0,
                )
            )
        return fresh
