import logging
from contextlib import contextmanager
from time import sleep

from celery import Celery
from elasticsearch import Elasticsearch
from minio import Minio
from redis import StrictRedis

from common.celery_app import BaseTask
from common.elasticsearch import init_elasticsearch
from common.messages.pubsub_service import PubSubService
from common.services.celery_inspect_service import CeleryInspectService
from common.services.imap_service import IMAPService
from common.services.lazybytes_service import LazyBytesService
from common.services.query_builder import QueryBuilder
from common.settings import settings
from common.utils.flush_s3_bucket import flush_s3_bucket

logger = logging.getLogger(__name__)

WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S = 0.1


class WipeService:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        celery_app: "Celery[BaseTask]",
        elasticsearch: Elasticsearch,
        query_builder: QueryBuilder,
        pubsub_service: PubSubService,
        redis_client: StrictRedis,
        redis_cache_client: StrictRedis,
        s3_intake_client: Minio,
        file_storage_service: LazyBytesService,
        lazybytes_service: LazyBytesService,
        imap_service: IMAPService,
        celery_inspect_service: CeleryInspectService,
    ):
        self._celery_app = celery_app
        self._elasticsearch = elasticsearch
        self._query_builder = query_builder
        self._pubsub_service = pubsub_service
        self._redis_client = redis_client
        self._redis_cache_client = redis_cache_client
        self._s3_intake_client = s3_intake_client
        self._file_storage_service = file_storage_service
        self._lazybytes_service = lazybytes_service
        self._imap_service = imap_service
        self._celery_inspect_service = celery_inspect_service

    def wipe_celery(self) -> None:
        logger.info("Wiping: celery")
        celery_control = self._celery_app.control
        while True:
            # purge all tasks until no celery worker has active tasks
            logger.info("Purging celery tasks")
            celery_control.purge()
            # wait for celery to be idle
            # send termination signal for all remaining tasks
            # these are most likely tasks which are backing off
            # at the workers.
            for task in self._celery_inspect_service.iterate_tasks():
                task_id = task.get("id", None)
                if isinstance(task_id, str):
                    logger.info("Terminating task: %s", task_id)
                    celery_control.terminate(task_id)
            if self._celery_inspect_service.is_idle():
                break
            sleep(WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S)

    def wipe_elasticsearch(self) -> None:
        logger.info("Wiping: elasticsearch")

        def set_destructive_requires_name(required: bool):
            self._elasticsearch.cluster.put_settings(
                transient={"action": {"destructive_requires_name": required}}
            )

        @contextmanager
        def allow_destructive_without_name():
            set_destructive_requires_name(False)
            try:
                yield
            finally:
                set_destructive_requires_name(True)

        with allow_destructive_without_name():
            self._elasticsearch.indices.delete(index="*")

        init_elasticsearch(self._query_builder, self._pubsub_service, True)

        # Using this would be faster, but doesn't fully work :(
        # self._elasticsearch.delete_by_query(index="*", body={"query": {"match_all": {}}})

    def wipe_redis(self) -> None:
        logger.info("Wiping: redis")
        self._redis_client.flushall()
        self._redis_cache_client.flushall()

    def wipe_s3(self) -> None:
        logger.info("Wiping: crawled buckets")
        bucket_name = settings.s3_storage.bucket_name
        logger.info("Clearing bucket: %s", bucket_name)
        flush_s3_bucket(self._s3_intake_client, bucket_name)

    def wipe_file_storage(self) -> None:
        logger.info("Wiping: file storage service")
        self._file_storage_service.flush()

    def wipe_lazybytes(self) -> None:
        logger.info("Wiping: lazybytes service")
        self._lazybytes_service.flush()

    def wipe_imap(self) -> None:
        logger.info("Wiping: IMAP")
        self._imap_service.wipe()
