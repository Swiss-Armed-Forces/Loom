import logging

from common.dependencies import init as init_common_dependencies

from crawler.dependencies import get_s3_client, init
from crawler.s3_crawler import S3Crawler
from crawler.settings import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init_common_dependencies()
    init()
    s3_client = get_s3_client()
    s3_crawler = S3Crawler(s3_client, settings.s3_bucket_names)
    # Start crawling
    s3_crawler.crawl()
