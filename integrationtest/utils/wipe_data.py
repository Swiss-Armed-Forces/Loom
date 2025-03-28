#!/usr/bin/env python3

import logging
from contextlib import contextmanager
from imaplib import IMAP4
from time import sleep

from common.dependencies import (
    get_celery_app,
    get_elasticsearch,
    get_pubsub_service,
    get_query_builder,
    get_redis_client,
)
from common.dependencies import init as init_common_dependencies
from common.elasticsearch import init_elasticsearch
from crawler.dependencies import get_minio_client, init
from crawler.settings import settings as crawler_settings
from pymongo import MongoClient

from utils.celery_inspect import is_celery_idle
from utils.settings import settings

logger = logging.getLogger(__name__)

WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S = 0.1
IMAP_TIMEOUT__S = 30


class WipeException(Exception):
    pass


def wipe_data():
    _wipe_imap()
    _wipe_celery()
    _wipe_mongo()
    _wipe_elasticsearch()
    _wipe_redis()
    _wipe_minio_buckets()


def _wipe_imap():
    logger.info("Wiping: IMAP")
    with IMAP4(
        settings.imap_host.host if settings.imap_host.host is not None else "",
        timeout=IMAP_TIMEOUT__S,
    ) as imap:
        imap.login(settings.imap_user, settings.imap_password)

        # List all mailboxes
        status, mailboxes = imap.list()
        if status != "OK":
            raise WipeException("Failed to retrieve mailboxes.")

        # Delete all mailboxes
        for mailbox in mailboxes:
            if not isinstance(mailbox, bytes):
                continue
            mailbox_name = mailbox.decode().split(' "/" ')[-1].strip('"')
            imap.delete(mailbox_name)


def _wipe_celery():
    logger.info("Wiping: celery")
    celery_control = get_celery_app().control
    while True:
        # purge all tasks until no celery worker has active tasks
        celery_control.purge()
        if is_celery_idle():
            break
        sleep(WAIT_FOR_CELERY_IDLE_SLEEP_TIME__S)


MONGO_PRESERVE_DBS = ["admin", "config", "local"]


def _wipe_mongo():
    logger.info("Wiping: mongodb")
    client = MongoClient(str(settings.mongo_db_host))
    for db in client.list_database_names():
        if db not in MONGO_PRESERVE_DBS:
            client.drop_database(db)


def _wipe_elasticsearch():
    logger.info("Wiping: elasticsearch")

    def set_destructive_requires_name(required: bool):
        get_elasticsearch().cluster.put_settings(
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
        get_elasticsearch().indices.delete(index="*")

    init_elasticsearch(get_query_builder(), get_pubsub_service(), True)

    # Using this would be faster, but doesn't fully work :(
    # get_elasticsearch().delete_by_query(index="*", body={"query": {"match_all": {}}})


def _wipe_redis():
    redis_client = get_redis_client()
    redis_client.flushall()


def _wipe_minio_buckets():
    logger.info("Wiping: MinIO")
    client = get_minio_client()
    buckets = client.list_buckets()
    for bucket in buckets:
        logger.info("Wiping bucket: %s", bucket.name)
        objects = client.list_objects(bucket.name, include_version=True, recursive=True)
        for bucket_object in objects:
            if bucket_object.object_name:
                client.remove_object(
                    bucket.name, bucket_object.object_name, bucket_object.version_id
                )
        if bucket.name != crawler_settings.minio_default_bucket_name:
            client.remove_bucket(bucket.name)


if __name__ == "__main__":
    init_common_dependencies()
    init()
    wipe_data()
