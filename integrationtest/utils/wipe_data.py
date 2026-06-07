#!/usr/bin/env python3

import logging

from common.dependencies import get_wipe_service
from common.dependencies import init as init_common_dependencies
from worker.dependencies import init as init_worker_dependencies

logger = logging.getLogger(__name__)


def wipe_data():
    service = get_wipe_service()
    service.wipe_celery()
    service.wipe_rabbit()
    service.wipe_elasticsearch()
    service.wipe_redis()
    service.wipe_intake()
    service.wipe_file_storage()
    service.wipe_lazybytes()
    service.wipe_imap()


if __name__ == "__main__":
    init_common_dependencies()
    init_worker_dependencies()
    wipe_data()
