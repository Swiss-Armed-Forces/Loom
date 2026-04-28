import logging
import random
from abc import ABC
from datetime import datetime, timedelta
from pprint import pformat
from typing import Any

import celery
from celery import Celery, Task, chord
from celery import group as original_group
from celery import signals
from celery.canvas import Signature
from celery.schedules import crontab
from kombu import Exchange, Queue, serialization
from pydantic import BaseModel, Field, RootModel

from common.settings import CELERY_QUEUE_NAME_MAXLEN, settings
from common.utils.cgroup_memory_limit import (
    MemoryLimitNotFoundError,
    get_cgroup_memory_limit,
)
from common.utils.oom_score_adjust import adjust_oom_score
from common.utils.sharding import get_all_persister_shards

logger = logging.getLogger(__name__)


def _never_nowfun():
    return datetime(year=1970, month=1, day=1, hour=0)


CELERY_SCHEDULE_NEVER = crontab(
    minute="0",
    hour="1",
    nowfun=_never_nowfun,
)


def get_beat_schedule() -> dict:
    """Return the Celery Beat schedule configuration.

    This function is separate from init_celery_app() so it can be called at module level
    by other components (e.g., beat router) without requiring a fully initialized Celery
    app.
    """
    return {
        # Magick trick: use prime numbers for all */X tasks -> then we will have less conflicts
        "shrink-cache": {
            "task": "worker.periodic.shrink_periodically_task.shrink_periodically_task",
            "schedule": crontab(minute="*/3"),
        },
        "cleanup-on-idle": {
            "task": "worker.periodic.flush_on_idle_task.flush_on_idle_task",
            "schedule": crontab(minute="*/11"),
        },
        "reindex-lost-files-on-idle": {
            "task": (
                "worker.periodic.reindex_lost_files_on_idle_task.reindex_lost_files_on_idle_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="5", hour="22-05"),
        },
        "hide-old-uploaded-files": {
            "task": "worker.periodic.hide_periodically_task.hide_periodically_task",
            "schedule": crontab(minute="0", hour="0"),
        },
        "unsubscribe-old-imap-folders": {
            "task": (
                "worker.periodic.unsubscribe_old_imap_folders_periodically_task.unsubscribe_old_imap_folders_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="30", hour="0"),
        },
        "sync-flagged-emails": {
            "task": (
                "worker.periodic.sync_flagged_emails_periodically_task.sync_flagged_emails_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": CELERY_SCHEDULE_NEVER,
        },
        # SeaweedFS Maintenance Tasks - frequent "on-idle" variants (check_idle=True)
        "seaweedfs-fix-replication-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="35", hour="0,5,10,15,20"),
            "args": ("volume.fix.replication", ["-apply"]),
        },
        "seaweedfs-balance-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="35", hour="1,6,11,16,21"),
            "args": ("volume.balance", ["-apply"]),
        },
        "seaweedfs-scrub-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="35", hour="2,7,12,17,22"),
            "args": ("volume.scrub",),
        },
        "seaweedfs-s3-clean-uploads-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="35", hour="3,8,13,18,23"),
            "args": ("s3.clean.uploads",),
        },
        "seaweedfs-vacuum-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="35", hour="4,9,14,19"),
            "args": ("volume.vacuum", "-garbageThreshold=0.01"),
        },
        # SeaweedFS Maintenance Tasks - weekly forced runs at night (check_idle=False)
        "seaweedfs-fix-replication": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="0", day_of_week="6"),
            "args": ("volume.fix.replication", ["-apply"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-balance": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="2", day_of_week="6"),
            "args": ("volume.balance", ["-apply"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-scrub": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="0", day_of_week="0"),
            "args": ("volume.scrub",),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-s3-clean-uploads": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="2", day_of_week="0"),
            "args": ("s3.clean.uploads",),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-vacuum": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="4", day_of_week="0,6"),
            "args": ("volume.vacuum", "-garbageThreshold=0.01"),
            "kwargs": {"check_idle": False},
        },
    }


class DeadTask(Exception):
    """Exception raised when a task comes from a dead letter queue."""


class XDeathEntry(BaseModel):
    queue: str
    reason: str
    count: int
    exchange: str
    routing_keys: list[str] = Field(alias="routing-keys")
    # AMQP 0.9.1:
    time: datetime | None = None
    # AMQP 1.0:
    first_time: datetime | None = Field(alias="first-time", default=None)
    last_time: datetime | None = Field(alias="last-time", default=None)


class XDeathHeader(RootModel[list[XDeathEntry]]):
    def __getitem__(self, item) -> XDeathEntry:
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


class BaseTask(ABC, Task):
    def __call__(self, *args, **kwargs) -> None:
        headers = getattr(self.request, "headers", {}) or {}

        # x-death is an AMQP 0.9.1 header set by RabbitMQ when a message is dead-lettered
        x_death = XDeathHeader.model_validate(headers.get("x-death", []))
        if len(x_death) > 1:
            # More than one death: reap the task
            raise DeadTask(f"Task died: {x_death}")

        return self.run(*args, **kwargs)


def _patch_group(app: "Celery[BaseTask]") -> None:
    """Patch the behavior of celery of group/chain nesting.

    See: https://github.com/celery/celery/issues/8182
    """

    def patched_group(*signatures: Signature[Any], **options: Any) -> Signature[Any]:
        """A patch for celery.group This is required, because celery does not work as
        expected when using a mixture of nested groups & chains."""
        return chord(original_group(*signatures, **options), __completer.s())

    @app.task()
    def __completer(results):
        """Task that does nothing, can be used in a chord to complete the chord."""
        return results

    celery.group = patched_group  # type: ignore[misc, assignment]


def _get_shared_exchange() -> Exchange:
    # All queues share one exchange.
    # Using a single exchange means delayed_delivery only
    return Exchange(
        name=settings.celery_default_exchange_name,
        type=settings.celery_default_exchange_type,
        delivery_mode="persistent",
        passive=False,
        durable=True,
        auto_delete=False,
        arguments={"alternate-exchange": settings.celery_alternate_exchange_name},
    )


def _get_alternate_exchange() -> Exchange:
    return Exchange(
        name=settings.celery_alternate_exchange_name,
        type=settings.celery_alternate_exchange_type,
        delivery_mode="persistent",
        passive=False,
        durable=True,
        auto_delete=False,
    )


def _get_queue(name: str) -> Queue:
    queue_name = f"{settings.celery_queue_name_prefix}{name}"
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_shared_exchange(),
        routing_key=name,
        passive=False,
        durable=True,
        auto_delete=False,
        queue_arguments={
            # We are using Quorum Queues in order to profit from the
            # broker's poison message handling mechanism and thus avoid
            # processing poison messages repeatedly.
            #
            # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
            "x-queue-type": "quorum",
            "x-delivery-limit": settings.celery_deliver_limit,
            "x-dead-letter-exchange": settings.celery_default_exchange_name,
            "x-dead-letter-routing-key": settings.celery_graveyard_task_name,
        },
    )


def _get_unroutable_queue() -> Queue:
    queue_name = (
        f"{settings.celery_queue_name_prefix}{settings.celery_unroubtable_task_name}"
    )
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_alternate_exchange(),
        routing_key="*",
        passive=False,
        durable=True,
        auto_delete=False,
        queue_arguments={
            # We are using Quorum Queues in order to profit from the
            # broker's poison message handling mechanism and thus avoid
            # processing poison messages repeatedly.
            #
            # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
            "x-queue-type": "quorum",
            "x-message-ttl": settings.celery_unroubtable_ttl__seconds * 1000,
        },
    )


def _get_graveyard_queue() -> Queue:
    queue_name = (
        f"{settings.celery_queue_name_prefix}{settings.celery_graveyard_task_name}"
    )
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_shared_exchange(),
        routing_key=settings.celery_graveyard_task_name,
        passive=False,
        durable=True,
        auto_delete=False,
        queue_arguments={
            # We are using Quorum Queues in order to profit from the
            # broker's poison message handling mechanism and thus avoid
            # processing poison messages repeatedly.
            #
            # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
            "x-queue-type": "quorum",
            "x-delivery-limit": settings.celery_graveyard_deliver_limit,
            "x-dead-letter-exchange": settings.celery_default_exchange_name,
            "x-dead-letter-routing-key": settings.celery_dead_task_name,
        },
    )


def _get_dead_queue() -> Queue:
    queue_name = f"{settings.celery_queue_name_prefix}{settings.celery_dead_task_name}"
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_shared_exchange(),
        routing_key=settings.celery_dead_task_name,
        passive=False,
        durable=True,
        auto_delete=False,
        queue_arguments={
            # We are using Quorum Queues in order to profit from the
            # broker's poison message handling mechanism and thus avoid
            # processing poison messages repeatedly.
            #
            # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
            "x-queue-type": "quorum",
        },
    )


def init_celery_app() -> "Celery[BaseTask]":  # pylint: disable=too-many-statements
    """Initialize a minimal Celery app."""
    app = Celery(
        "loom",
        broker=str(settings.celery_broker_host),
        backend=str(settings.celery_backend_host),
        task_cls=BaseTask,
    )

    # Configure content and serializers
    app.conf.accept_content = ["json", "pickle"]
    app.conf.result_accept_content = [
        "json",
        "pickle",
    ]
    app.conf.event_serializer = "pickle"
    app.conf.result_serializer = "pickle"
    app.conf.task_serializer = "pickle"
    serialization.register_pickle()
    serialization.enable_insecure_serializers()

    # Enable compression for tasks & result backend
    # We do this to reduce bandwidth usage, memory
    # and disk pressure on the broker and backend.
    # Using bzip2 for better compression ratio since we can
    # scale workers horizontally easier than the backend.
    #
    # Note: result_compression currently has no effect with Redis backend
    # (only task_compression works), but we keep it configured anyway in case
    # future Celery versions add support for compressing result messages in Redis.
    app.conf.task_compression = "bzip2"
    app.conf.result_compression = "bzip2"

    # Prevent Celery from hijacking the root logger configuration.
    # We manage our own logging setup and don't want Celery to override it.
    app.conf.worker_hijack_root_logger = False

    # We do use the prefork pool here, because it is
    # a) more robust against worker failure
    # b) splits signalling and task processing (worker online)
    app.conf.worker_pool = "prefork"
    app.conf.worker_concurrency = settings.worker_max_concurrency
    # Set max memory per child worker to prevent memory leaks which
    # might lead to OOM-Kills
    try:
        app.conf.worker_max_memory_per_child = (get_cgroup_memory_limit() / 1024) // (
            app.conf.worker_concurrency + 1  # +1: for main Process
        )
    except MemoryLimitNotFoundError:
        # we don't set a memory limit if we can not determine the Cgroup memory limit
        pass

    # Note: that worker_prefetch_multiplier applies per queue, which means
    # in our model (one queue per task) the worker will still prefetch quite
    # a few tasks.
    app.conf.worker_prefetch_multiplier = 1

    # We do set only the soft time limit here, for a hard time limit we use
    # RabbitMQ consumer_timeout to rely on the task being re-delived to a different
    # worker.
    app.conf.task_soft_time_limit = int(settings.task_time_limit__seconds * 0.98)
    app.conf.task_time_limit = None

    app.conf.task_acks_late = True
    app.conf.task_track_started = True
    app.conf.task_send_sent_event = True
    app.conf.worker_send_task_events = True

    app.conf.task_default_queue_type = "quorum"
    app.conf.worker_detect_quorum_queues = True
    app.conf.broker_transport_options = {"confirm_publish": True}

    # We have to disable task_ignore_result as we heavily rely on chors
    # https://docs.celeryq.dev/en/stable/userguide/canvas.html#important-notes
    app.conf.task_ignore_result = False
    app.conf.task_store_errors_even_if_ignored = True
    app.conf.result_backend_always_retry = True
    app.conf.task_acks_on_failure_or_timeout = True
    app.conf.task_reject_on_worker_lost = False

    # Set result expiration to a very large value (9999 days) for the following reasons:
    #
    # 1. We want results to effectively never expire under normal conditions:
    #    - Expired results = Redis evicts the result
    #    - Evicted results = task pipeline stops mid-execution
    #    - This causes files to remain stuck in "starting" state indefinitely
    #
    # 2. However, we MUST set a non-zero TTL (not 0/None) because:
    #    - We use maxmemory-policy=volatile-ttl in Redis
    #    - This policy only evicts keys WITH a TTL when memory pressure occurs
    #    - Without TTL, results would never be evicted, leading to Redis OOM crashes
    #
    # 3. Trade-off decision:
    #    - A few files failing to finish processing (due to eviction) is acceptable
    #    - Redis crashing is catastrophic and affects the entire system
    #    - Under memory pressure, evicting old task results is the lesser evil
    #
    # The large value (9999 days ~ 274 years) ensures results persist long enough
    # for normal operations while still being eligible for eviction if Redis
    # runs out of memory.
    app.conf.result_expires = timedelta(days=99999)

    # Register periodic tasks
    app.conf.beat_schedule = get_beat_schedule()

    # Task queues & routes setup
    app.conf.task_queues = []
    app.conf.task_routes = {}
    # Define the celery default queues & routes
    # This queue will be used when external components
    # without insight about all the tasks send tasks
    # to celery.
    #
    # For example, the api will post to this queue.
    default_queue = _get_queue(settings.celery_default_task_name)
    app.conf.task_queues.append(default_queue)
    app.conf.task_routes[settings.celery_default_task_name] = {
        "routing_key": settings.celery_default_task_name
    }

    app.conf.task_default_queue = default_queue.name
    app.conf.task_default_routing_key = settings.celery_default_task_name
    app.conf.task_default_exchange = settings.celery_default_exchange_name
    app.conf.task_default_exchange_type = settings.celery_default_exchange_type
    app.conf.task_default_delivery_mode = "persistent"

    # We want to be implicit here: Disable auto queue creation
    app.conf.task_create_missing_queues = False

    # Define dead letter queues
    graveyard_queue = _get_graveyard_queue()
    app.conf.task_queues.append(graveyard_queue)
    app.conf.task_routes[settings.celery_graveyard_task_name] = {
        "routing_key": settings.celery_graveyard_task_name
    }
    dead_queue = _get_dead_queue()
    app.conf.task_queues.append(dead_queue)
    app.conf.task_routes[settings.celery_dead_task_name] = {
        "routing_key": settings.celery_dead_task_name
    }

    # Define unroutable queues
    unroutable_queue = _get_unroutable_queue()
    app.conf.task_queues.append(unroutable_queue)
    app.conf.task_routes[settings.celery_unroubtable_task_name] = {"routing_key": "*"}

    # Define persister shard queues for serialized persistence per entity
    for persister_shard_name in get_all_persister_shards(settings.num_persister_shards):
        persister_shard_queue = _get_queue(persister_shard_name)
        app.conf.task_queues.append(persister_shard_queue)
        app.conf.task_routes[persister_shard_name] = {
            "routing_key": persister_shard_name
        }

    # Worker type specific configuration
    match settings.worker_type:
        case "REAPER":
            # We have to disable concurrency and prefetching here (=1),
            # because we will be consuming tasks in the dead-letter queue
            # and we have to process them one-by-one.
            app.conf.worker_concurrency = 1
            app.conf.worker_prefetch_multiplier = 1
        case "PERSISTER":
            # Persister workers run with concurrency=1 to ensure sequential
            # processing per shard, avoiding optimistic concurrency control
            # conflicts. However, we can safely prefetch many tasks.
            app.conf.worker_concurrency = 1
            app.conf.worker_prefetch_multiplier = 16
            # Do not restart child processes
            app.conf.worker_max_memory_per_child = None
            app.conf.worker_max_tasks_per_child = None
        case _:
            pass

    # We shuffle the task queue order at startup to reduce the risk of starvation or overload
    # on specific queues. Celery sets a prefetch limit per queue, not globally - so when a
    # worker subscribes to many queues, it prefetches one task *from each queue*. This can
    # result in many tasks being reserved even if concurrency is low.
    #
    # If a worker crashes, all of those prefetched tasks are requeued, and their
    # x-delivery-count (used for retry/dead-letter logic) is incremented. If one queue
    # contains tasks that often crash the worker, and Celery always polls that queue first,
    # it can effectively stall the pipeline and repeatedly retry the same crashing tasks.
    #
    # By randomizing the queue order at each startup, we distribute the likelihood of any
    # one queue dominating the prefetching pattern, helping to balance task execution and
    # avoid failure feedback loops tied to queue order.
    random.shuffle(app.conf.task_queues)

    # Patch the celery group functionality as required due to a bug in celery.
    _patch_group(app=app)

    # Ensure this app is used for unpickling operations (fixes hostname resolution issues)
    app.set_current()  # Thread-local current app
    app.set_default()  # Global default app

    logging.debug("Celery initialized with config: %s", pformat(app.conf))
    return app


def _register_task_queues(app: Celery):
    """Create a dedicated queue per task.

    Args:
        app: The Celery app instance.
    """
    from worker.utils.persisting_task import (  # pylint: disable=import-outside-toplevel
        PersistingTaskBase,
    )

    for task_name, task in app.tasks.items():
        if isinstance(task, PersistingTaskBase):
            # do not register persisting tasks
            continue

        queue = _get_queue(task_name)
        app.conf.task_queues.append(queue)
        app.conf.task_routes[task_name] = {"routing_key": task_name}
        logger.info("Added Queue for task: %s", task_name)


def register_tasks_for_package(app: Celery, package: str):
    app.conf.update(
        include=[f"{package}.tasks"],
    )
    app.autodiscover_tasks([package], force=True)
    _register_task_queues(app)
    # See comment in: init_celery_app
    random.shuffle(app.conf.task_queues)


# Set oom scores for the pool worker
# such that the pool worker is more likely to be
# killed under memory pressure..
@signals.worker_process_init.connect
def set_oom_score_for_pool_worker(*_, **__):
    adjust_oom_score(1000)


@signals.task_prerun.connect
def log_task_start(
    _: Task | None = None,
    task_id: str | None = None,
    task: Task | None = None,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    **__: Any,
) -> None:
    logger.info(
        "Starting task %s[%s] with args=%s, kwargs=%s",
        task.name if task is not None else None,
        task_id,
        args,
        kwargs,
    )
