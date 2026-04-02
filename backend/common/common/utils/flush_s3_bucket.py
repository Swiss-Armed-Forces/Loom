import logging
from datetime import datetime, timedelta, timezone

from minio import Minio
from minio.deleteobjects import DeleteObject

logger = logging.getLogger(__name__)


def flush_s3_bucket(
    client: Minio,
    bucket_name: str,
    min_age: timedelta | None = None,
) -> None:
    """Clear objects from an S3 bucket without deleting the bucket itself.

    This approach is required for SeaweedFS compatibility:
    - SeaweedFS does not properly clean up when buckets are deleted
    - Clearing objects instead of removing the bucket is idempotent and reliable

    Args:
        client: The Minio client to use
        bucket_name: The name of the bucket to clear
        min_age: Only delete objects older than this. If None, delete all objects.
    """
    if not client.bucket_exists(bucket_name):
        return

    objects = client.list_objects(bucket_name, recursive=True)

    if min_age is not None:
        cutoff_time = datetime.now(timezone.utc) - min_age
        delete_objects = (
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

    errors = client.remove_objects(bucket_name, delete_objects)
    for error in errors:
        logger.error("Failed to delete object %s: %s", error.name, error.message)
