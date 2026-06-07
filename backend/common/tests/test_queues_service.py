# pylint: disable=redefined-outer-name
from typing import Any

import pytest

from common.dependencies import get_redis_client
from common.services.queues_service import QUEUE_PAUSED_KEY_PREFIX, QueuesService

_QUEUE = "test-queue"
_KEY = f"{QUEUE_PAUSED_KEY_PREFIX}:{_QUEUE}"


@pytest.fixture()
def queues_service() -> QueuesService:
    return QueuesService(
        rabbit_mq_management_host="http://mock/",
        redis_client=get_redis_client(),
    )


def test_set_queue_paused_sets_redis_key(queues_service: QueuesService):
    redis: Any = get_redis_client()

    queues_service.set_queue_paused(_QUEUE, True)

    redis.set.assert_called_once_with(_KEY, "1")


def test_set_queue_resumed_deletes_redis_key(queues_service: QueuesService):
    redis: Any = get_redis_client()

    queues_service.set_queue_paused(_QUEUE, False)

    redis.delete.assert_called_once_with(_KEY)


def test_is_queue_paused_returns_true_when_key_exists(queues_service: QueuesService):
    redis: Any = get_redis_client()
    redis.exists.return_value = 1

    assert queues_service.is_queue_paused(_QUEUE) is True
    redis.exists.assert_called_once_with(_KEY)


def test_is_queue_paused_returns_false_when_key_absent(queues_service: QueuesService):
    redis: Any = get_redis_client()
    redis.exists.return_value = 0

    assert queues_service.is_queue_paused(_QUEUE) is False


def test_get_paused_queues_returns_queue_names(queues_service: QueuesService):
    redis: Any = get_redis_client()
    prefix = f"{QUEUE_PAUSED_KEY_PREFIX}:"
    redis.keys.return_value = [
        f"{prefix}queue-a".encode(),
        f"{prefix}queue-b".encode(),
    ]

    result = queues_service.get_paused_queues()

    assert set(result) == {"queue-a", "queue-b"}
    redis.keys.assert_called_once_with(f"{prefix}*")


def test_get_paused_queues_returns_empty_when_none_paused(
    queues_service: QueuesService,
):
    redis: Any = get_redis_client()
    redis.keys.return_value = []

    assert queues_service.get_paused_queues() == []
