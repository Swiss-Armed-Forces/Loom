# pylint: disable=redefined-outer-name
from typing import Any

import pytest

from common.dependencies import get_redis_client
from common.services.queues_service import PAUSED_QUEUES_SET_KEY, QueuesService

_QUEUE = "test-queue"


@pytest.fixture()
def queues_service() -> QueuesService:
    return QueuesService(
        rabbit_mq_management_host="http://mock/",
        redis_client=get_redis_client(),
    )


def test_set_queue_paused_adds_to_index(queues_service: QueuesService):
    redis: Any = get_redis_client()

    queues_service.set_queue_paused(_QUEUE, True)

    redis.sadd.assert_called_once_with(PAUSED_QUEUES_SET_KEY, _QUEUE)


def test_set_queue_resumed_removes_from_index(queues_service: QueuesService):
    redis: Any = get_redis_client()

    queues_service.set_queue_paused(_QUEUE, False)

    redis.srem.assert_called_once_with(PAUSED_QUEUES_SET_KEY, _QUEUE)


def test_is_queue_paused_returns_true_when_member(queues_service: QueuesService):
    redis: Any = get_redis_client()
    redis.sismember.return_value = 1

    assert queues_service.is_queue_paused(_QUEUE) is True
    redis.sismember.assert_called_once_with(PAUSED_QUEUES_SET_KEY, _QUEUE)


def test_is_queue_paused_returns_false_when_not_member(queues_service: QueuesService):
    redis: Any = get_redis_client()
    redis.sismember.return_value = 0

    assert queues_service.is_queue_paused(_QUEUE) is False


def test_get_paused_queues_returns_queue_names(queues_service: QueuesService):
    redis: Any = get_redis_client()
    redis.smembers.return_value = {b"queue-a", b"queue-b"}

    result = queues_service.get_paused_queues()

    assert set(result) == {"queue-a", "queue-b"}
    redis.smembers.assert_called_once_with(PAUSED_QUEUES_SET_KEY)


def test_get_paused_queues_returns_empty_when_none_paused(
    queues_service: QueuesService,
):
    redis: Any = get_redis_client()
    redis.smembers.return_value = set()

    assert queues_service.get_paused_queues() == []
