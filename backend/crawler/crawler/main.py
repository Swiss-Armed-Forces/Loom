import logging

from common.dependencies import init as init_common_dependencies

from crawler.dependencies import get_minio_client, init
from crawler.minio_crawler import MinioCrawler
from crawler.settings import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init_common_dependencies()
    init()
    minio_client = get_minio_client()
    minio_crawler = MinioCrawler(minio_client, settings.minio_bucket_names)
    # Start crawling
    minio_crawler.crawl()
