import dataclasses
import logging
import random
import re
from abc import ABC
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from pprint import pformat
from typing import (
    Any,
    Protocol,
    get_args,
    get_origin,
    get_type_hints,
)

import celery
from celery import Celery, Task, bootsteps, chord
from celery import group as original_group
from celery import signals
from celery.canvas import Signature
from celery.schedules import crontab
from kombu import Exchange, Queue, serialization
from pydantic import BaseModel, Field, RootModel

from common.services.lazybytes_service import LazyBytes, TempStorageTag
from common.settings import CELERY_QUEUE_NAME_MAXLEN, WorkerType, settings
from common.utils.cgroup_memory_limit import (
    MemoryLimitNotFoundError,
    get_cgroup_memory_limit,
)
from common.utils.oom_score_adjust import adjust_oom_score
from common.utils.sharding import get_all_persister_shards

logger = logging.getLogger(__name__)

# The alternate exchange (ae-loom) must be fanout, not topic.
#
# When the loom exchange cannot route a message it forwards the message to
# ae-loom with the original routing key intact. If ae-loom were a topic
# exchange, the loom:unroutable binding would need a pattern that matches every
# possible routing key. "*" only matches single-word keys, so dotted Celery
# task names (e.g. "worker.foo.bar_task") would be silently dropped. "#"
# would work but is fragile if additional queues are ever bound to ae-loom.
#
# A fanout exchange delivers unconditionally to all bound queues, so the
# routing key is irrelevant — every unroutable message lands in loom:unroutable
# regardless of its name, with no pattern to maintain.
_ALTERNATE_EXCHANGE_TYPE = "fanout"

# Fraction of task_time_limit_seconds used as the Celery soft time limit (see below).
_SOFT_TIME_LIMIT_RATIO = 0.98


def get_beat_schedule() -> dict:
    """Return the Celery Beat schedule configuration.

    This function is separate from init_celery_app() so it can be called at module level
    by other components (e.g., beat router) without requiring a fully initialized Celery
    app.
    """
    return {
        # Magic trick: use prime numbers for all */X tasks -> then we will have less conflicts
        "compute-complete-estimate": {
            "task": (
                "worker.periodic.compute_complete_estimate_task.compute_complete_estimate_task"
            ),
            "schedule": crontab(minute="*/1"),
        },
        "throttle-and-flush-lazybytes": {
            "task": (
                "worker.periodic.throttle_and_flush_lazybytes_task.throttle_and_flush_lazybytes_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="*/2"),
        },
        "shrink-cache": {
            "task": "worker.periodic.shrink_periodically_task.shrink_periodically_task",
            "schedule": crontab(minute="*/3"),
        },
        "reindex-lost-files-on-idle": {
            "task": (
                "worker.periodic.reindex_lost_files_on_idle_task.reindex_lost_files_on_idle_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="11", hour="22-05"),
        },
        "hide-old-uploaded-files": {
            "task": "worker.periodic.hide_periodically_task.hide_periodically_task",
            "schedule": crontab(minute="0", hour="0"),
        },
        "flush-root-task-info-on-idle": {
            "task": (
                "worker.periodic.flush_root_task_info_on_idle_task.flush_root_task_info_on_idle_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="0", hour="3"),
        },
        "unsubscribe-old-imap-folders": {
            "task": (
                "worker.periodic.unsubscribe_old_imap_folders_periodically_task.unsubscribe_old_imap_folders_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="30", hour="0"),
        },
        "sync-imap-flags": {
            "task": (
                "worker.periodic.sync_imap_flags_periodically_task.sync_imap_flags_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="0", hour="2"),
        },
        # SeaweedFS Maintenance Tasks - frequent "on-idle" variants (check_idle=True)
        "seaweedfs-fix-replication-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="0-23/6"),
            "args": ("volume.fix.replication", ["-apply"]),
        },
        "seaweedfs-balance-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="1-23/6"),
            "args": ("volume.balance", ["-apply"]),
        },
        "seaweedfs-scrub-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="2-23/6"),
            "args": ("volume.scrub",),
        },
        "seaweedfs-s3-clean-uploads-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="3-23/6"),
            "args": ("s3.clean.uploads",),
        },
        "seaweedfs-vacuum-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="4-23/6"),
            "args": ("volume.vacuum", ["-garbageThreshold=0.01"]),
        },
        "seaweedfs-fsck-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="5-23/6"),
            "args": (
                "volume.fsck",
                [
                    "-findMissingChunksInFiler=true",
                    "-reallyDeleteFromVolume=true",
                    "-reallyDeleteFilerEntries=true",
                ],
            ),
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
            "args": ("volume.vacuum", ["-garbageThreshold=0.01"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-fsck": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="6", day_of_week="0,6"),
            "args": (
                "volume.fsck",
                [
                    "-findMissingChunksInFiler=true",
                    "-reallyDeleteFromVolume=true",
                    "-reallyDeleteFilerEntries=true",
                ],
            ),
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


# Kombu NDL routing key format: 28 binary digits separated by dots, then a dot,
# then the original routing key.  Example (countdown=3):
#   "0000000000000000000000000011.loom:my_task"
# Each retry through NDL prepends another 56-character prefix, so after ~4
# retries the routing key exceeds AMQP's 255-byte shortstr limit and Celery
# raises struct.error.  We strip the prefix in BaseTask.__call__ so that
# signature_from_request() always copies the original routing key into the
# next retry message.
_NDL_ROUTING_KEY_RE = re.compile(r"^[01](?:\.[01]){27}\.(.+)$")


class TaskGroupName(str, Enum):
    ALL = "all"
    PROCESSING = "processing"
    PERSISTING = "persisting"
    PERIODIC = "periodic"
    DISPATCH = "dispatch"
    LAZYBYTES_PRODUCING = "lazybytes_producing"
    LAZYBYTES_CONSUMING = "lazybytes_consuming"
    LAZYBYTES_CONSUMING_PRODUCING = "lazybytes_consuming_producing"


_task_groups: dict[TaskGroupName, list[str]] = {}


def register_task(group_name: TaskGroupName, task_name: str) -> None:
    """Register a task name into a named group."""
    _task_groups.setdefault(group_name, []).append(task_name)


def task_group(group_name: TaskGroupName) -> Callable[[Task], Task]:
    """Register a Celery task into a named group.

    Apply as the outermost decorator so the Celery task object (with .name) is
    received:

        @task_group(TaskGroupName.DISPATCH)
        @app.task()
        def my_task(...): ...
    """

    def decorator(task: Task) -> Task:
        _task_groups.setdefault(group_name, []).append(task.name)
        return task

    return decorator


def _has_temp_lazybytes_type(hint: Any) -> bool:
    """Return True if hint contains a TempStorageTag-flavoured LazyBytes anywhere."""
    origin = get_origin(hint)
    if origin is not None:
        if isinstance(origin, type) and issubclass(origin, LazyBytes):
            return TempStorageTag in get_args(hint)
        return any(_has_temp_lazybytes_type(arg) for arg in get_args(hint))
    # Pydantic generic models (e.g. LazyBytes[TempStorageTag]) are concrete classes,
    # not typing aliases, so get_origin() returns None. Check Pydantic's own metadata.
    pydantic_meta = getattr(hint, "__pydantic_generic_metadata__", None)
    if pydantic_meta is not None:
        pydantic_origin = pydantic_meta.get("origin")
        pydantic_args = pydantic_meta.get("args", ())
        if isinstance(pydantic_origin, type) and issubclass(pydantic_origin, LazyBytes):
            return TempStorageTag in pydantic_args
    # Plain Pydantic models: recurse into field annotations.
    if isinstance(hint, type) and issubclass(hint, BaseModel):
        return any(
            _has_temp_lazybytes_type(field.annotation)
            for field in hint.model_fields.values()
            if field.annotation is not None
        )
    # Dataclasses: recurse into field annotations.
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return any(_has_temp_lazybytes_type(h) for h in get_type_hints(hint).values())
    return False


def register_if_lazybytes_task(task: type[Task]) -> None:
    """Register task in the appropriate LAZYBYTES_* group based on type hints.

    - LAZYBYTES_PRODUCING: return type has temp lazybytes, params do not.
      Pure sources; throttled under lazybytes pressure to stop new lazybytes
      from being created.
    - LAZYBYTES_CONSUMING: params have temp lazybytes (regardless of return type).
      Waited for before flushing; not throttled even if they also produce, since
      throttling them while waiting for them to drain would deadlock.
    """
    try:
        hints = get_type_hints(task.run)
    except Exception:  # pylint: disable=broad-except
        return
    return_hint = hints.get("return")
    param_hints = {k: v for k, v in hints.items() if k != "return"}
    produces = return_hint is not None and _has_temp_lazybytes_type(return_hint)
    consumes = any(_has_temp_lazybytes_type(h) for h in param_hints.values())
    if produces and not consumes:
        register_task(TaskGroupName.LAZYBYTES_PRODUCING, task.name)
    if produces and consumes:
        register_task(TaskGroupName.LAZYBYTES_CONSUMING_PRODUCING, task.name)
    if consumes and not produces:
        register_task(TaskGroupName.LAZYBYTES_CONSUMING, task.name)


class BaseTask(ABC, Task):
    _task_group_name: TaskGroupName | None = None

    @classmethod
    def on_bound(cls, app: Celery) -> None:
        super().on_bound(app)
        register_task(TaskGroupName.ALL, cls.name)
        if cls._task_group_name is not None:
            register_task(cls._task_group_name, cls.name)
        register_if_lazybytes_task(cls)

    def __call__(self, *args, **kwargs) -> None:
        headers = getattr(self.request, "headers", {}) or {}

        x_death = XDeathHeader.model_validate(headers.get("x-death", []))

        # Remove x-death from headers before calling run(). Celery's retry() copies
        # self.request.headers into each new retry message; without removal, celery_delayed_N
        # entries accumulate across NDL retries and interfere with RabbitMQ's x-delivery-count
        # tracking. Removing x-death entirely is safe: RabbitMQ ignores x-death on published
        # messages and sets its own on dead-lettering.
        headers.pop("x-death", None)
        x_death = XDeathHeader(
            root=[d for d in x_death.root if not d.queue.startswith("celery_delayed")]
        )

        # Strip NDL routing key prefix from delivery_info so that retry()
        # publishes a clean routing key instead of a growing binary prefix chain.
        delivery_info = getattr(self.request, "delivery_info", {}) or {}
        if m := _NDL_ROUTING_KEY_RE.match(delivery_info.get("routing_key", "")):
            delivery_info["routing_key"] = m.group(1)

        # Raise DeadTask only when the message has previously been dead-lettered out of
        # the graveyard queue — i.e. it already went through graveyard processing.
        graveyard_queue = (
            f"{settings.celery_queue_name_prefix}{settings.celery_graveyard_task_name}"
        )
        if any(d.queue == graveyard_queue for d in x_death.root):
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
        type=_ALTERNATE_EXCHANGE_TYPE,
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
        f"{settings.celery_queue_name_prefix}{settings.celery_unroutable_task_name}"
    )
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_alternate_exchange(),
        routing_key="",  # fanout exchange ignores the routing key
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
            "x-message-ttl": settings.celery_unroutable_ttl__seconds * 1000,
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
            "x-delivery-limit": settings.celery_dead_deliver_limit,
            "x-dead-letter-exchange": settings.celery_default_exchange_name,
            "x-dead-letter-routing-key": settings.celery_abyss_task_name,
        },
    )


def _get_abyss_queue() -> Queue:
    queue_name = f"{settings.celery_queue_name_prefix}{settings.celery_abyss_task_name}"
    queue_name = queue_name[:CELERY_QUEUE_NAME_MAXLEN]
    return Queue(
        name=queue_name,
        exchange=_get_shared_exchange(),
        routing_key=settings.celery_abyss_task_name,
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
            # Messages that could not be processed even from the dead queue (e.g. the reaper
            # was OOM-killed during deserialization) end up here. No worker consumes this
            # queue; messages expire after the configured TTL.
            "x-message-ttl": settings.celery_abyss_ttl__seconds * 1000,
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

    # We set only the soft time limit here; for a hard time limit we rely on
    # RabbitMQ's consumer_timeout to redeliver the task to a different worker.
    # The soft limit fires slightly before consumer_timeout, giving the
    # SoftTimeLimitExceeded handler time to clean up and ack before redelivery.
    app.conf.task_soft_time_limit = int(
        settings.task_time_limit_seconds * _SOFT_TIME_LIMIT_RATIO
    )
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
        "routing_key": settings.celery_default_task_name,
        "exchange_type": settings.celery_default_exchange_type,
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
        "routing_key": settings.celery_graveyard_task_name,
        "exchange_type": settings.celery_default_exchange_type,
    }
    dead_queue = _get_dead_queue()
    app.conf.task_queues.append(dead_queue)
    app.conf.task_routes[settings.celery_dead_task_name] = {
        "routing_key": settings.celery_dead_task_name,
        "exchange_type": settings.celery_default_exchange_type,
    }
    abyss_queue = _get_abyss_queue()
    app.conf.task_queues.append(abyss_queue)
    app.conf.task_routes[settings.celery_abyss_task_name] = {
        "routing_key": settings.celery_abyss_task_name,
        "exchange_type": settings.celery_default_exchange_type,
    }

    # The unroutable queue is intentionally NOT added to task_queues or
    # task_routes. Adding it would cause Celery's DelayedDelivery bootstep
    # (_bind_queues) to call bind_queue_to_native_delayed_delivery_exchange on
    # it, which — because the queue's routing_key is "*" — produces a
    # "#.*" binding from ae-loom onto celery_delayed_delivery. That wildcard
    # matches every delayed-retry message, creating a spurious copy in
    # loom:unroutable for each countdown-based retry.
    #
    # The queue itself is declared by declare_terminal_queues (worker_ready
    # signal) so the alternate-exchange routing still works correctly.

    # Register persister shard routes globally so any worker type can dispatch
    # to them. Queue *declaration* is deferred to register_persister_shard_queues()
    # which is called only by PERSISTER workers. Keeping the queues out of
    # task_queues for non-PERSISTER workers prevents Celery's delayed-delivery
    # binding bootstep from crashing on queues that are not yet declared in
    # RabbitMQ (see https://github.com/celery/celery/issues/9960).
    for persister_shard_name in get_all_persister_shards(settings.num_persister_shards):
        app.conf.task_routes[persister_shard_name] = {
            "routing_key": persister_shard_name,
            "exchange_type": settings.celery_default_exchange_type,
        }

    # Worker type specific configuration
    match settings.worker_type:
        case WorkerType.REAPER:
            # We have to disable concurrency and prefetching here (=1),
            # because we will be consuming tasks in the dead-letter queue
            # and we have to process them one-by-one.
            app.conf.worker_concurrency = 1
            app.conf.worker_prefetch_multiplier = 1
        case WorkerType.PERSISTER:
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
        app.conf.task_routes[task_name] = {
            "routing_key": task_name,
            "exchange_type": settings.celery_default_exchange_type,
        }
        logger.info("Added Queue for task: %s", task_name)


def register_tasks_for_package(app: Celery, package: str):
    app.conf.update(
        include=[f"{package}.tasks"],
    )
    app.autodiscover_tasks([package], force=True)
    _register_task_queues(app)
    # See comment in: init_celery_app
    random.shuffle(app.conf.task_queues)


def register_persister_shard_queues(app: "Celery[Any]") -> None:
    """Declare persister shard queues and add them to task_queues.

    Must be called only by PERSISTER workers. Shard queue routes are already registered
    globally in init_celery_app() so any worker can dispatch to them; this function
    handles the queue *declaration* side that is only needed on the workers that
    actually consume the queues.
    """
    for persister_shard_name in get_all_persister_shards(settings.num_persister_shards):
        persister_shard_queue = _get_queue(persister_shard_name)
        app.conf.task_queues.append(persister_shard_queue)


def make_queue_guard(is_allowed: Callable[[str], bool]) -> type:
    """Return a Consumer bootstep that blocks dynamic queue subscriptions.

    Usage::

        app.steps['consumer'].add(make_queue_guard(lambda q: q in allowed_set))

    Wraps ``consumer.add_task_queue`` on the Consumer instance at startup via
    Celery's official bootstep extension API. Any subsequent ``add_consumer``
    control command for a queue where ``is_allowed`` returns False is silently
    dropped with an info log.

    Note: the pidbox ``add_consumer`` panel command calls
    ``consumer.add_task_queue`` (via ``call_soon``), so this is the correct
    intercept point — not ``add_consumer`` or ``add_queue``.

    This prevents broadcast ``add_consumer`` signals (e.g. from throttle resume)
    from causing workers to consume queues outside their designated scope.
    """

    class _QueueGuardStep(bootsteps.StartStopStep):
        def start(self, parent: Any) -> None:
            _orig = parent.add_task_queue

            def _guarded(queue: Any, *args: Any, **kw: Any) -> Any:
                if not is_allowed(queue):
                    logger.info(
                        "Ignoring add_task_queue for queue %r "
                        "(not in this worker's allowed set)",
                        queue,
                    )
                    return None
                return _orig(queue, *args, **kw)

            parent.add_task_queue = _guarded

    return _QueueGuardStep


# Set oom scores for the pool worker
# such that the pool worker is more likely to be
# killed under memory pressure..
@signals.worker_process_init.connect
def set_oom_score_for_pool_worker(*_, **__):
    adjust_oom_score(1000)


def get_terminal_queues() -> list[Queue]:
    """Return all terminal queues — queues that no worker consumes."""
    return [_get_abyss_queue(), _get_unroutable_queue()]


class _WorkerReadySender(Protocol):  # pylint: disable=too-few-public-methods
    # The celery-stubs package does not type the `app` attribute on
    # celery.worker.components.Consumer (the actual runtime sender of
    # worker_ready), nor does the kombu-stubs package type
    # ProducerPool.acquire. This Protocol captures the subset we actually
    # use so mypy/Pyright can follow the chain.
    # Remove once upstream stubs are complete.
    app: Celery


@signals.worker_ready.connect
def declare_terminal_queues(sender: _WorkerReadySender, **__: Any) -> None:
    """Declare terminal queues that no worker consumes.

    Celery only declares queues a worker actively subscribes to. The abyss and
    unroutable queues are terminal destinations with no consumers, so they must be
    declared explicitly to ensure dead-letter and alternate-exchange routing works
    correctly on fresh deployments.
    """
    with sender.app.pool.acquire(block=True) as conn:  # type: ignore[attr-defined]
        for queue in get_terminal_queues():
            queue(conn.default_channel).declare()  # type: ignore[operator]


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
