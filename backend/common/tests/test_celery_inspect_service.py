from typing import Any
from unittest.mock import MagicMock

from common.dependencies import get_celery_app, get_redis_client
from common.services.celery_inspect_service import (
    QUEUE_PAUSED_KEY_PREFIX,
    CeleryInspectService,
)
from common.services.queues_service import QueuesService

_QUEUE = "test-queue"
_KEY = f"{QUEUE_PAUSED_KEY_PREFIX}:{_QUEUE}"


def _make_service() -> CeleryInspectService:
    return CeleryInspectService(
        celery_app=get_celery_app(),
        queues_service=MagicMock(spec=QueuesService),
        redis_client=get_redis_client(),
    )


def test_set_queue_paused_sets_redis_key_and_broadcasts():
    redis: Any = get_redis_client()
    celery_app: Any = get_celery_app()

    _make_service().set_queue_paused(_QUEUE, True)

    redis.set.assert_called_once_with(_KEY, "1")
    celery_app.control.cancel_consumer.assert_called_once_with(_QUEUE, reply=True)


def test_set_queue_resumed_deletes_redis_key_and_broadcasts():
    redis: Any = get_redis_client()
    celery_app: Any = get_celery_app()

    _make_service().set_queue_paused(_QUEUE, False)

    redis.delete.assert_called_once_with(_KEY)
    celery_app.control.add_consumer.assert_called_once_with(_QUEUE, reply=True)


def test_is_queue_paused_returns_true_when_key_exists():
    redis: Any = get_redis_client()
    redis.exists.return_value = 1

    assert _make_service().is_queue_paused(_QUEUE) is True
    redis.exists.assert_called_once_with(_KEY)


def test_is_queue_paused_returns_false_when_key_absent():
    redis: Any = get_redis_client()
    redis.exists.return_value = 0

    assert _make_service().is_queue_paused(_QUEUE) is False


def test_get_paused_queues_returns_queue_names():
    redis: Any = get_redis_client()
    prefix = f"{QUEUE_PAUSED_KEY_PREFIX}:"
    redis.keys.return_value = [
        f"{prefix}queue-a".encode(),
        f"{prefix}queue-b".encode(),
    ]

    result = _make_service().get_paused_queues()

    assert set(result) == {"queue-a", "queue-b"}
    redis.keys.assert_called_once_with(f"{prefix}*")


def test_get_paused_queues_returns_empty_when_none_paused():
    redis: Any = get_redis_client()
    redis.keys.return_value = []

    assert _make_service().get_paused_queues() == []
