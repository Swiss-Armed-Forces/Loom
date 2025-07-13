import logging
import random
from abc import ABC
from typing import Any

from celery import Celery, Task, signals
from celery.schedules import crontab
from kombu import Exchange, Queue, serialization

from common.settings import settings
from common.utils.oom_score_adjust import adjust_oom_score

logger = logging.getLogger(__name__)

CELERY_QUEUE_NAME_PREFIX = "celery"
CELERY_DEAD_LETTER_QUEUE_NAME_SUFFIX = ".dead_letter"


def get_queues_for_task(task_name: str) -> list[Queue]:
    queue_name = task_name
    dead_letter_queue_name = f"{queue_name}{CELERY_DEAD_LETTER_QUEUE_NAME_SUFFIX}"

    return [
        Queue(
            task_name,
            Exchange(task_name, delivery_mode="persistent"),
            routing_key=task_name,
            queue_arguments={
                # We are using Quorum Queues in order to profit from the
                # broker's poison message handling mechanism and thus avoid
                # processing poison messages repeatedly.
                #
                # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
                "x-queue-type": "quorum",
                "x-delivery-limit": 10,
                "x-dead-letter-exchange": dead_letter_queue_name,
                "x-dead-letter-routing-key": dead_letter_queue_name,
            },
        ),
        Queue(
            dead_letter_queue_name,
            Exchange(dead_letter_queue_name, delivery_mode="persistent"),
            routing_key=dead_letter_queue_name,
            queue_arguments={
                # We are using Quorum Queues in order to profit from the
                # broker's poison message handling mechanism and thus avoid
                # processing poison messages repeatedly.
                #
                # https://www.rabbitmq.com/docs/quorum-queues#poison-message-handling
                "x-queue-type": "quorum",
                "x-delivery-limit": 1,
            },
        ),
    ]


class DeadTask(Exception):
    """Exception raised when a task comes from a dead letter queue."""


class BaseTask(ABC, Task):
    def __call__(self, *args, **kwargs):
        headers = getattr(self.request, "headers", {}) or {}
        xdeath = headers.get("x-death")

        # x-death is an AMQP 0.9.1 header set by RabbitMQ when a message is dead-lettered
        if xdeath:
            # Optional: you can still check for count/reason/queue if needed
            reason = xdeath[0].get("reason", "unknown")
            raise DeadTask(f"Rejecting task due to x-death header (reason: {reason})")

        return self.run(*args, **kwargs)


def init_minimal_celery_app() -> Celery:
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

    app.conf.worker_hijack_root_logger = True
    # We do use the prefork pool here, becasue it is
    # a) more robust against worker failure
    # b) splits signalling and task processing (worker online)
    app.conf.worker_pool = "prefork"

    # We have to disable concurrency and prefetching here (=1),
    # since in case of a hard worker failure only tasks which were
    # unacked will have it's x-delivery-count incremented and eventually
    # moved to the dead letter queue.
    # Note that worker_prefetch_multiplier applies per queue, which means
    # in our model (one queue per task) the worker will still prefetch quite
    # a few tasks.
    app.conf.worker_concurrency = 1
    app.conf.worker_prefetch_multiplier = 1

    app.conf.task_acks_late = True
    app.conf.task_track_started = True
    app.conf.task_send_sent_event = True
    app.conf.worker_send_task_events = True

    app.conf.task_default_queue_type = "quorum"
    app.conf.worker_detect_quorum_queues = True
    app.conf.broker_transport_options = {"confirm_publish": True}

    app.conf.task_ignore_result = True
    app.conf.task_store_errors_even_if_ignored = True
    app.conf.result_backend_max_retries = 30
    app.conf.task_acks_on_failure_or_timeout = True
    app.conf.task_reject_on_worker_lost = False

    # Register periodic tasks
    app.conf.beat_schedule = {
        "cleanup-on-idle": {
            "task": "worker.periodic.flush_on_idle_task.flush_on_idle_task",
            "schedule": crontab(minute="*/15"),
        },
        "shrink-cache": {
            "task": "worker.periodic.shrink_periodically_task.shrink_periodically_task",
            "schedule": crontab(minute="*"),
        },
    }

    # Define the celery default queue
    # This queue will be used when external components
    # without insight about all the tasks send tasks
    # to celery.
    #
    # For example, the api will post to this queue.
    app.conf.task_queues = get_queues_for_task("celery")

    return app


def init_celery_app() -> Celery:
    """Initialize and configure the Celery app."""
    app = init_minimal_celery_app()
    register_queues(
        app=app,
    )

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
    return app


def register_queues(app: Celery):
    """Create a dedicated queue per task.

    Args:
        app: The Celery app instance.
    """

    task_queues: list[Queue] = app.conf.task_queues or []
    task_routes = app.conf.task_routes or {}

    for task_name in app.tasks.keys():
        queue_name = f"{CELERY_QUEUE_NAME_PREFIX}:{task_name}"

        if queue_name in {q.name for q in task_queues}:
            # do not add duplicate queues
            continue

        logger.info("Adding Queue: %s", queue_name)

        task_queues.extend(get_queues_for_task(queue_name))
        task_routes[task_name] = {"queue": queue_name}

    app.conf.task_queues = task_queues
    app.conf.task_routes = task_routes


def register_queues_for_package(app: Celery, package: str):
    app.conf.update(
        include=[f"{package}.tasks"],
    )
    app.autodiscover_tasks([package], force=True)
    register_queues(app=app)


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
