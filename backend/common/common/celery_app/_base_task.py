import re
from abc import ABC

from celery import Celery, Task

from common.celery_app._dead_letter import DeadTask, XDeathHeader
from common.celery_app._task_groups import TaskGroupName, register_task
from common.settings import settings

# Kombu NDL routing key format: 28 binary digits separated by dots, then a dot,
# then the original routing key.  Example (countdown=3):
#   "0000000000000000000000000011.loom:my_task"
# Each retry through NDL prepends another 56-character prefix, so after ~4
# retries the routing key exceeds AMQP's 255-byte shortstr limit and Celery
# raises struct.error.  We strip the prefix in BaseTask.__call__ so that
# signature_from_request() always copies the original routing key into the
# next retry message.
_NDL_ROUTING_KEY_RE = re.compile(r"^[01](?:\.[01]){27}\.(.+)$")


class BaseTask(ABC, Task):
    _task_group_name: TaskGroupName | None = None

    @classmethod
    def on_bound(cls, app: Celery) -> None:
        super().on_bound(app)
        register_task(TaskGroupName.ALL, cls.name)
        if cls._task_group_name is not None:
            register_task(cls._task_group_name, cls.name)

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
