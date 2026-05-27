import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import islice
from typing import Iterator, TypeVar

from minio import Minio
from minio.deleteobjects import DeleteError, DeleteObject

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

_S3_MAX_DELETE_BATCH_SIZE = 1000


@dataclass(frozen=True)
class _DeleteResult:
    deleted: int
    failures: int
    batch_count: int


def _chunks(iterable: Iterator[_T], size: int) -> Iterator[list[_T]]:
    """Yield successive lists of up to `size` items from `iterable` without loading the
    full sequence into memory."""
    it = iter(iterable)
    while batch := list(islice(it, size)):
        yield batch


def _delete_batch(
    client: Minio,
    bucket_name: str,
    batch: list[DeleteObject],
) -> list[DeleteError]:
    """Send one S3 multi-delete request and return all errors as a list.

    Materialising the iterator returned by remove_objects() is required; the MinIO SDK
    drives the HTTP request lazily and will not report errors until the iterator is
    consumed.
    """
    return list(client.remove_objects(bucket_name, iter(batch)))


def _run_concurrent_deletes(
    client: Minio,
    bucket_name: str,
    delete_objects: Iterator[DeleteObject],
    batch_size: int,
    workers: int,
) -> _DeleteResult:
    """Submit delete batches concurrently and collect results."""
    total_deleted = 0
    total_failures = 0
    batch_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures: dict[Future[list[DeleteError]], int] = {}

        for batch in _chunks(delete_objects, batch_size):
            batch_count += 1
            future = executor.submit(_delete_batch, client, bucket_name, batch)
            futures[future] = len(batch)

        for future in as_completed(futures):
            submitted_count = futures[future]
            try:
                errors = future.result()
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "Batch delete request failed entirely (bucket=%s, objects=%d)",
                    bucket_name,
                    submitted_count,
                )
                total_failures += submitted_count
                continue

            total_deleted += submitted_count - len(errors)
            total_failures += len(errors)

            for error in errors:
                logger.error(
                    "Failed to delete object %s: %s (bucket=%s)",
                    error.name,
                    error.message,
                    bucket_name,
                )

            logger.debug(
                "Batch complete: deleted=%d failures=%d bucket=%s",
                submitted_count - len(errors),
                len(errors),
                bucket_name,
            )

    return _DeleteResult(
        deleted=total_deleted,
        failures=total_failures,
        batch_count=batch_count,
    )


def flush_s3_bucket(
    client: Minio,
    bucket_name: str,
    min_age: timedelta | None = None,
    *,
    workers: int = 32,
    batch_size: int = _S3_MAX_DELETE_BATCH_SIZE,
) -> None:
    """Clear objects from an S3 bucket without deleting the bucket itself.

    This approach is required for SeaweedFS compatibility:
    - SeaweedFS does not properly clean up when buckets are deleted
    - Clearing objects instead of removing the bucket is idempotent and reliable

    Delete requests are dispatched concurrently across `workers` threads, each
    carrying a full S3 multi-delete batch.  This dramatically improves
    throughput when SeaweedFS volumes are read-only and individual delete
    operations incur internal retry latency.

    Args:
        client: The Minio client to use.
        bucket_name: The name of the bucket to clear.
        min_age: Only delete objects older than this. If None, delete all objects.
        workers: Number of concurrent delete threads.
        batch_size: Objects per S3 multi-delete request (max 1000).
    """
    if not client.bucket_exists(bucket_name):
        return

    objects = client.list_objects(bucket_name, recursive=True)

    if min_age is not None:
        cutoff_time = datetime.now(timezone.utc) - min_age
        delete_objects: Iterator[DeleteObject] = (
            DeleteObject(obj.object_name)
            for obj in objects
            if obj.object_name is not None
            and obj.last_modified is not None
            and obj.last_modified < cutoff_time
        )
    else:
        delete_objects = (
            DeleteObject(obj.object_name)
            for obj in objects
            if obj.object_name is not None
        )

    effective_batch_size = min(batch_size, _S3_MAX_DELETE_BATCH_SIZE)
    start_time = time.monotonic()
    result = _run_concurrent_deletes(
        client, bucket_name, delete_objects, effective_batch_size, workers
    )
    elapsed = time.monotonic() - start_time

    logger.info(
        "Bucket flush complete: bucket=%s batches=%d deleted=%d failures=%d elapsed=%.2fs",
        bucket_name,
        result.batch_count,
        result.deleted,
        result.failures,
        elapsed,
    )
