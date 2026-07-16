from kombu import Exchange, Queue

from common.settings import CELERY_QUEUE_NAME_MAXLEN, settings

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


def get_terminal_queues() -> list[Queue]:
    """Return all terminal queues — queues that no worker consumes."""
    return [_get_abyss_queue(), _get_unroutable_queue()]
