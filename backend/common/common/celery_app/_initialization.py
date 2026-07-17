import logging
import random
from datetime import timedelta
from pprint import pformat

import celery
from celery import Celery
from celery import group as original_group
from celery.canvas import chord
from kombu import serialization

from common.celery_app._base_task import BaseTask
from common.celery_app._beat_schedule import get_beat_schedule
from common.celery_app._queues import (
    _get_abyss_queue,
    _get_dead_queue,
    _get_graveyard_queue,
    _get_queue,
)
from common.settings import WorkerType, settings
from common.utils.cgroup_memory_limit import (
    MemoryLimitNotFoundError,
    get_cgroup_memory_limit,
)
from common.utils.sharding import get_all_persister_shards

logger = logging.getLogger(__name__)

# Fraction of task_time_limit_seconds used as the Celery soft time limit (see below).
_SOFT_TIME_LIMIT_RATIO = 0.98


def _patch_group(app: "Celery[BaseTask]") -> None:
    """Patch the behavior of celery of group/chain nesting.

    See: https://github.com/celery/celery/issues/8182
    """

    @app.task()
    def noop(results):
        """Task that does nothing, can be used in a chord to complete the chord."""
        return results

    # pylint: disable=invalid-name
    class chordgroup(chord):
        def __init__(self, *tasks, **options):
            super().__init__(
                header=original_group(*tasks, **options),
                body=noop.s(),
            )

    celery.group = chordgroup  # type: ignore


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
