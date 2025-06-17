"""Celery app factory."""

import logging

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue, serialization

from common.settings import settings

logger = logging.getLogger(__name__)

CELERY_QUEUE_MIN_PRIORITY = 0
CELERY_QUEUE_MAX_PRIORITY = 10


def init_celery_app() -> Celery:
    """Returns a configured celery app instance."""
    app = Celery(
        "loom",
        broker=str(settings.celery_broker_host),
        backend=str(settings.celery_backend_host),
    )

    # Use pickle
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

    # Define Queues
    app.conf.task_queues = [
        Queue(
            "celery",
            Exchange("celery", delivery_mode="persistent"),
            routing_key="celery",
            # NOTE:
            # - All these arguments will only be working with the
            #   RabbitMQ message broker
            # - The x-queue-mode should not be required after switching
            #   to rabbitmq 3.12, but we keep it here just to be safe
            queue_arguments={
                "x-queue-mode": "lazy",
                "x-max-priority": CELERY_QUEUE_MAX_PRIORITY,
            },
        ),
        Queue(
            "celery.intreactive",
            Exchange("celery.intreactive", delivery_mode="persistent"),
            routing_key="celery.intreactive",
            # NOTE:
            # - All these arguments will only be working with the
            #   RabbitMQ message broker
            # - The x-queue-mode should not be required after switching
            #   to rabbitmq 3.12, but we keep it here just to be safe
            queue_arguments={
                "x-queue-mode": "lazy",
            },
        ),
        Queue(
            "celery.__periodic",
            Exchange("celery.__periodic", delivery_mode="persistent"),
            routing_key="celery.__periodic",
            # NOTE:
            # - All these arguments will only be working with the
            #   RabbitMQ message broker
            # - The x-queue-mode should not be required after switching
            #   to rabbitmq 3.12, but we keep it here just to be safe
            queue_arguments={
                "x-queue-mode": "lazy",
            },
        ),
        Queue(
            "celery.__meta",
            Exchange("celery.__meta", delivery_mode="persistent"),
            routing_key="celery.__meta",
            # NOTE:
            # - All these arguments will only be working with the
            #   RabbitMQ message broker
            # - The x-queue-mode should not be required after switching
            #   to rabbitmq 3.12, but we keep it here just to be safe
            queue_arguments={
                "x-queue-mode": "lazy",
            },
        ),
    ]
    # We use priority queues [0,CELERY_QUEUE_MAX_PRIORITY] -> set default priority to average
    app.conf.task_default_priority = int(CELERY_QUEUE_MAX_PRIORITY // 2)

    # Route all periodic tasks to the periodic queue
    app.conf.task_routes = {"worker.periodic.*": {"queue": "celery.__periodic"}}

    # Register all periodic tasks
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

    # Result expires after X seconds
    # app.conf.result_expires = 300

    # Do not keep task results, just errors
    app.conf.task_ignore_result = True
    app.conf.task_store_errors_even_if_ignored = True

    # Store tasks and results compressed
    # app.conf.task_compression = "gzip"
    # app.conf.result_compression = "gzip"

    # Give up saving after X retries
    app.conf.result_backend_max_retries = 30

    # Only ack a task after completion
    app.conf.task_acks_late = True
    app.conf.task_acks_on_failure_or_timeout = True

    # only run one task at the time, this is so that
    # in case this process is killed due to limits
    # only one task is killed.
    app.conf.worker_concurrency = 1
    # but prefetch quite a few at once to keep
    # the worker thread/process always busy
    app.conf.worker_prefetch_multiplier = 128

    # We can not reject tasks on worker lost, because
    # we have some non-idempotent tasks in the pipeline.
    # If thos tasks never finish because of a timeout
    # or OOM-Killer we can not retry.
    # task_reject_on_worker_lost = False is the default,
    # but I am leaving this here for documentation
    # purposes.
    app.conf.task_reject_on_worker_lost = False

    return app
