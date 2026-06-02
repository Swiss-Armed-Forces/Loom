"""Provides the worker entry point."""

import logging
import sys
from shlex import quote

from celery import signals
from common.celery_app import register_persister_shard_queues
from common.dependencies import get_celery_app, get_celery_inspect_service
from common.dependencies import init as init_common_dependencies
from common.settings import settings
from common.utils.sharding import (
    get_all_persister_shards,
    get_persister_shard_for_worker,
)

from worker.dependencies import init

logger = logging.getLogger(__name__)


def init_all():
    init_common_dependencies()
    init()


# Runs for each worker subprocess
@signals.worker_process_init.connect
def pool_worker_main(*_, **__):
    init_all()


@signals.worker_ready.connect
def restore_queue_pause_state(sender, **__):
    """Cancel consumption of any queues that are currently paused in Redis.

    Celery's cancel_consumer broadcast only reaches currently running workers. This
    handler ensures a newly started worker also stops consuming from any queue that was
    paused before it started.
    """
    paused = get_celery_inspect_service().get_paused_queues()
    if not paused:
        return
    celery_app = get_celery_app()
    for queue in paused:
        logger.info("Queue %s is paused; cancelling consumer on this worker", queue)
        celery_app.control.cancel_consumer(
            queue, destination=[sender.hostname], reply=True
        )


# Initial load (parent process)
init_all()


# Required for celery auto discovery
app = get_celery_app()

argv = sys.argv[1:]


def get_queue_from_task(task: str) -> str:
    return f"{settings.celery_queue_name_prefix}{task}"


match settings.worker_type:
    case "WORKER":
        # Exclude graveyard, dead, and persister shard queues from normal workers
        all_persister_shards = get_all_persister_shards(settings.num_persister_shards)
        all_persister_queues = [
            get_queue_from_task(shard) for shard in all_persister_shards
        ]
        exclude_queues = [
            get_queue_from_task(settings.celery_graveyard_task_name),
            get_queue_from_task(settings.celery_dead_task_name),
            get_queue_from_task(settings.celery_unroutable_task_name),
            get_queue_from_task(settings.celery_abyss_task_name),
        ] + all_persister_queues
        argv = argv + [
            "--exclude-queues",
            ",".join(exclude_queues),
            "--autoscale",
            f"{settings.worker_max_concurrency},{settings.worker_min_concurrency}",
        ]
    case "REAPER":
        argv = argv + [
            "--queues",
            ",".join(
                [
                    get_queue_from_task(settings.celery_graveyard_task_name),
                    get_queue_from_task(settings.celery_dead_task_name),
                ]
            ),
            "--autoscale",
            "1,0",
        ]
    case "PERSISTER":
        # Declare persister shard queues in RabbitMQ and register them in
        # task_queues. This is done here (not in init_celery_app) so that
        # non-PERSISTER workers never see these queues in task_queues and
        # the delayed-delivery binding bootstep doesn't fail on undeclared
        # queues (https://github.com/celery/celery/issues/9960).
        register_persister_shard_queues(app)
        # Persister workers only consume their assigned shard queues
        this_persister_shards = get_persister_shard_for_worker(
            settings.persister_id,
            settings.persister_total,
            settings.num_persister_shards,
        )
        this_persister_queues = [
            get_queue_from_task(shard) for shard in this_persister_shards
        ]
        argv = argv + [
            "--queues",
            ",".join(this_persister_queues),
        ]
    case "FLOWER":
        argv = argv + [
            f"--broker-api={settings.rabbit_mq_management_host}api/",
            "--purge_offline_workers=600",
            "--max_tasks=50000",
        ]
    case "BEAT":
        argv = argv + [
            "--scheduler",
            "heartbeat_scheduler:HeartbeatScheduler",
        ]
    case _:
        pass


logger.info(
    "Starting (%s): %s", settings.worker_type, " ".join(quote(arg) for arg in argv)
)
app.start(argv=argv)
