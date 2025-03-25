import logging

from common.dependencies import get_minio_client, init

from crawler.minio_crawler import MinioCrawler

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init()

    minio_client = get_minio_client()
    minio_crawler = MinioCrawler(minio_client)

    minio_crawler.crawl()
