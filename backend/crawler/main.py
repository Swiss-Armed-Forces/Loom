import logging

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_s3_intake_client,
    get_task_scheduling_service,
)

from crawler.dependencies import init
from crawler.imap_notify_listener_service import IMAPNotifyListenerService
from crawler.s3_crawler import S3Crawler
from crawler.settings import CrawlerType, settings

logger = logging.getLogger(__name__)

init()

match settings.crawler_type:
    case CrawlerType.S3_CRAWLER:
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
        s3_crawler.crawl()
    case CrawlerType.NOTIFY_LISTENER:
        _service = IMAPNotifyListenerService(
            host=str(settings.imap_host.host or ""),
            port=int(settings.imap_host.port or 143),
            user=settings.imap_user,
            password=settings.imap_password,
            file_repository=get_file_repository(),
            file_scheduling_service=get_file_scheduling_service(),
        )
        logger.info("Starting IMAP NOTIFY listener")
        _service.run()
