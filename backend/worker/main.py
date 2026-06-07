"""Provides the worker entry point."""

import logging
import sys
from typing import Protocol

from celery import signals
from common.celery_app import (
    get_terminal_queues,
    make_queue_guard,
    register_persister_shard_queues,
)
from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
)
from common.dependencies import init as init_common_dependencies
from common.settings import CELERY_QUEUE_NAME_MAXLEN, WorkerType, settings
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
def publish_task_groups(**__):
    """Publish in-process task group registrations to Redis so the API can read them."""
    get_celery_inspect_service().register_task_groups()


class _WorkerReadySender(Protocol):  # pylint: disable=too-few-public-methods
    # The celery-stubs package does not type the `hostname` attribute on
    # celery.worker.components.Consumer (the actual runtime sender of
    # worker_ready). This Protocol captures the subset we actually use so
    # mypy/Pyright can follow the chain.
    # Remove once upstream stubs are complete.
    hostname: str


@signals.worker_ready.connect
def on_worker_ready(sender: _WorkerReadySender, **__):
    """Cancel consumers for paused queues on this newly started worker.

    Celery's cancel_consumer broadcast only reaches currently running workers. This
    ensures a newly started worker also stops consuming any queue that was paused before
    it came online.
    """
    get_celery_inspect_service().restore_pause_state_on_worker([sender.hostname])


# Initial load (parent process)
init_all()


# Required for celery auto discovery
app = get_celery_app()

argv = sys.argv[1:]


def get_queue_from_task(task: str) -> str:
    return f"{settings.celery_queue_name_prefix}{task}"[:CELERY_QUEUE_NAME_MAXLEN]


match settings.worker_type:
    case WorkerType.WORKER:
        # Exclude graveyard, dead, and persister shard queues from normal workers
        all_persister_shards = get_all_persister_shards(settings.num_persister_shards)
        all_persister_queues = [
            get_queue_from_task(shard) for shard in all_persister_shards
        ]
        exclude_queues = [
            get_queue_from_task(settings.celery_graveyard_task_name),
            get_queue_from_task(settings.celery_dead_task_name),
            *[q.name for q in get_terminal_queues()],
        ] + all_persister_queues
        argv = argv + [
            "--exclude-queues",
            ",".join(exclude_queues),
            "--autoscale",
            f"{settings.worker_max_concurrency},{settings.worker_min_concurrency}",
        ]
        _disallowed = frozenset(exclude_queues)
        app.steps["consumer"].add(make_queue_guard(lambda q: q not in _disallowed))
    case WorkerType.REAPER:
        _reaper_queues = [
            get_queue_from_task(settings.celery_graveyard_task_name),
            get_queue_from_task(settings.celery_dead_task_name),
        ]
        argv = argv + [
            "--queues",
            ",".join(_reaper_queues),
            "--autoscale",
            "1,0",
        ]
        _reaper_set = frozenset(_reaper_queues)
        app.steps["consumer"].add(make_queue_guard(lambda q: q in _reaper_set))
    case WorkerType.PERSISTER:
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
        _persister_set = frozenset(this_persister_queues)
        app.steps["consumer"].add(make_queue_guard(lambda q: q in _persister_set))
    case WorkerType.FLOWER:
        argv = argv + [
            f"--broker-api={settings.rabbit_mq_management_host}api/",
            "--purge_offline_workers=600",
            "--max_tasks=50000",
        ]
    case WorkerType.BEAT:
        argv = argv + [
            "--scheduler",
            "heartbeat_scheduler:HeartbeatScheduler",
        ]
    case _:
        pass


logger.info("Starting (%s): %s", settings.worker_type, " ".join(argv))
app.start(argv=argv)
