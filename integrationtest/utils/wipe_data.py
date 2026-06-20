#!/usr/bin/env python3

import logging
from concurrent.futures import ThreadPoolExecutor

from common.dependencies import get_wipe_service
from worker.dependencies import init as init_worker_dependencies

logger = logging.getLogger(__name__)


def wipe_data():
    service = get_wipe_service()
    service.wipe_celery()
    service.wipe_rabbit()
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(service.wipe_elasticsearch),
            executor.submit(service.wipe_redis),
            executor.submit(service.wipe_intake),
            executor.submit(service.wipe_file_storage),
            executor.submit(service.wipe_lazybytes),
            executor.submit(service.wipe_imap),
        ]
    for future in futures:
        future.result()


if __name__ == "__main__":
    init_worker_dependencies()
    wipe_data()
