import logging

from common.dependencies import get_lazybytes_service, get_s3_intake_client
from common.dependencies import init as init_common_dependencies

from crawler.s3_crawler import S3Crawler
from crawler.settings import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init_common_dependencies()
    s3_client = get_s3_intake_client()
    s3_crawler = S3Crawler(
        s3_client,
        settings.s3_storage.bucket_name,
        settings.s3_bucket_alias,
        get_lazybytes_service(),
    )
    # Start crawling
    s3_crawler.crawl()
