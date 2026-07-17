import logging
import random
from collections.abc import Callable
from typing import Any

from celery import Celery, bootsteps

from common.celery_app._queues import _get_queue
from common.settings import settings
from common.utils.sharding import get_all_persister_shards

logger = logging.getLogger(__name__)


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
