import logging

from common.dependencies import (
    get_file_storage_service,
    get_s3_intake_client,
    get_task_scheduling_service,
)

from crawler.dependencies import init
from crawler.s3_crawler import S3Crawler
from crawler.settings import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init()
    logger.info(
        "Initializing S3Crawler — bucket: '%s', alias: '%s'",
        settings.intake_storage.bucket_name,
        settings.s3_bucket_alias,
    )
    s3_client = get_s3_intake_client()
    s3_crawler = S3Crawler(
        s3_client,
        settings.intake_storage.bucket_name,
        settings.s3_bucket_alias,
        get_file_storage_service(),
        get_task_scheduling_service(),
    )
    # Start crawling
    s3_crawler.crawl()
