"""S3 bucket initialization script.

Run as: python -m common.scripts.init_s3

Intended to be run as a Kubernetes Job (Helm post-install/post-upgrade hook) before any
application pods start. Creates all required S3 buckets if they do not already exist.
"""

import logging

from common.dependencies import (
    get_s3_file_storage_client,
    get_s3_intake_client,
    get_s3_lazybytes_client,
    init,
)
from common.settings import settings

logger = logging.getLogger(__name__)

init()

logger.info("Starting S3 bucket initialization")

for bucket, client in [
    (settings.file_storage.bucket_name, get_s3_file_storage_client()),
    (settings.lazybytes_storage.bucket_name, get_s3_lazybytes_client()),
    (settings.intake_storage.bucket_name, get_s3_intake_client()),
]:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info("Created bucket: %s", bucket)
    else:
        logger.info("Bucket already exists: %s", bucket)

logger.info("S3 bucket initialization complete")
