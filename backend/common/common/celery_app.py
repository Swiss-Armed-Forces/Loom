import logging

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue, serialization

from common.settings import settings

logger = logging.getLogger(__name__)

CELERY_QUEUE_NAME_PREFIX = "celery"
DEFAULT_QUEUE_ARGS = {
    # NOTE:
    # - All these arguments will only be working with the
    #   RabbitMQ message broker
    # - The x-queue-mode should not be required after switching
    #   to rabbitmq 3.12, but we keep it here just to be safe
    "x-queue-mode": "lazy",
}


def init_celery_app() -> Celery:
    """Initialize and configure the Celery app."""
    app = Celery(
        "loom",
        broker=str(settings.celery_broker_host),
        backend=str(settings.celery_backend_host),
    )

    # Configure content and serializers
    app.conf.accept_content = ["application/json", "application/x-python-serialize"]
    app.conf.result_accept_content = [
        "application/json",
        "application/x-python-serialize",
    ]
    app.conf.event_serializer = "pickle"
    app.conf.result_serializer = "pickle"
    app.conf.task_serializer = "pickle"
    serialization.register_pickle()
    serialization.enable_insecure_serializers()

    # Configure worker behavior
    app.conf.worker_pool = "prefork"
    app.conf.worker_concurrency = 1
    app.conf.task_ignore_result = True
    app.conf.task_store_errors_even_if_ignored = True
    app.conf.result_backend_max_retries = 30
    app.conf.task_acks_late = True
    app.conf.task_acks_on_failure_or_timeout = True
    app.conf.worker_prefetch_multiplier = 128
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

    app.conf.task_queues = [
        # Define the celery default queue
        # This queue will be used when external components
        # without insight about all the tasks send tasks
        # to celery.
        #
        # For example the api will post to this queue.
        Queue(
            "celery",
            Exchange("celery", delivery_mode="persistent"),
            routing_key="celery",
            queue_arguments=DEFAULT_QUEUE_ARGS,
        ),
    ]
    register_queues(
        app=app,
    )
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
        queue_args = dict(DEFAULT_QUEUE_ARGS)

        if queue_name in {q.name for q in task_queues}:
            # do not add duplicate queues
            continue

        logger.info("Adding Queue: %s", queue_name)

        task_queues.append(
            Queue(
                name=queue_name,
                exchange=Exchange(queue_name, delivery_mode="persistent"),
                routing_key=queue_name,
                queue_arguments=queue_args,
            )
        )
        task_routes[task_name] = {"queue": queue_name}

    app.conf.task_queues = task_queues
    app.conf.task_routes = task_routes


def register_queues_for_package(app: Celery, package: str):
    app.conf.update(
        include=[f"{package}.tasks"],
    )
    app.autodiscover_tasks([package], force=True)
    register_queues(app=app)
