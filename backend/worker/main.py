"""Provides the worker entry point."""

import logging
import sys
from shlex import quote

from celery import signals
from common.celery_app import CELERY_DEAD_QUEUE_NAME, CELERY_GRAVEYARD_QUEUE_NAME
from common.dependencies import get_celery_app
from common.dependencies import init as init_common_dependencies
from common.settings import settings
from common.utils.sharding import (
    get_all_persister_shard_queues,
    get_persister_shard_queues_for_worker,
)

from worker.dependencies import init

logger = logging.getLogger(__name__)


def init_all(subprocess_reinit: bool = False):
    init_common_dependencies(subprocess_reinit=subprocess_reinit)
    init(subprocess_reinit=subprocess_reinit)


# Runs for each worker subprocess
@signals.worker_process_init.connect
def pool_worker_main(*_, **__):
    # Only reinit fork-unsafe connections, not Celery/tasks
    init_all(subprocess_reinit=True)


# Initial load (parent process)
init_all(subprocess_reinit=False)


# Required for celery auto discovery
app = get_celery_app()

argv = sys.argv[1:]
persister_shard_queues = get_all_persister_shard_queues(settings.num_persister_shards)
match settings.worker_type:
    case "WORKER":
        # Exclude graveyard, dead, and persister shard queues from normal workers
        exclude_queues = [
            CELERY_GRAVEYARD_QUEUE_NAME,
            CELERY_DEAD_QUEUE_NAME,
            *persister_shard_queues,
        ]
        argv = argv + [
            "--exclude-queues",
            ",".join(exclude_queues),
            "--autoscale",
            f"{settings.worker_max_concurrency},0",
        ]
    case "REAPER":
        argv = argv + [
            "--queues",
            f"{CELERY_GRAVEYARD_QUEUE_NAME},{CELERY_DEAD_QUEUE_NAME}",
            "--autoscale",
            "1,0",
        ]
    case "PERSISTER":
        # Persister workers only consume their assigned shard queues
        my_queues = get_persister_shard_queues_for_worker(
            settings.persister_id,
            settings.persister_total,
            settings.num_persister_shards,
        )
        argv = argv + [
            "--queues",
            ",".join(my_queues),
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
