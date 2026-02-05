"""Provides the worker entry point."""

import logging
import sys
from shlex import quote

from common.celery_app import CELERY_DEAD_QUEUE_NAME, CELERY_GRAVEYARD_QUEUE_NAME
from common.dependencies import get_celery_app
from common.dependencies import init as init_common_dependencies
from common.settings import settings

from worker.dependencies import init

logger = logging.getLogger(__name__)


init_common_dependencies()
init()
# Required for celery auto discovery
app = get_celery_app()

argv = sys.argv[1:]
match settings.worker_type:
    case "WORKER":
        argv = argv + [
            "--exclude-queues",
            f"{CELERY_GRAVEYARD_QUEUE_NAME},{CELERY_DEAD_QUEUE_NAME}",
            "--autoscale",
            f"{settings.worker_max_concurrency},0",
        ]
    case "REAPER":
        argv = argv + [
            "--queues",
            f"{CELERY_GRAVEYARD_QUEUE_NAME},{CELERY_DEAD_QUEUE_NAME}",
            "--autoscale",
            f"{settings.worker_max_concurrency},0",
        ]
    case "FLOWER":
        argv = argv + [
            f"--broker-api={settings.rabbit_mq_management_host}api/",
            "--purge_offline_workers=600",
            "--max_tasks=50000",
        ]
    case _:
        pass

logger.info(
    "Starting (%s): %s", settings.worker_type, " ".join(quote(arg) for arg in argv)
)
app.start(argv=argv)
