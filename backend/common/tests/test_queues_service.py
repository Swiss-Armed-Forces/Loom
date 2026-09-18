# pylint: disable=redefined-outer-name
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

from common.dependencies import get_redis_client
from common.services.queues_service import PAUSED_QUEUES_SET_KEY, QueuesService

_QUEUE = "test-queue"
_LOOM_QUEUE = "loom:worker.index_file.dispatch_tasks.dispatch_index_file"
_DELAYED_QUEUE = "celery_delayed_27"


@pytest.fixture()
def session() -> Any:
    return MagicMock(spec=requests.Session)


@pytest.fixture()
def queues_service(session: Any) -> QueuesService:
    return QueuesService(
        rabbit_mq_management_host="http://mock/",
        redis_client=get_redis_client(),
        session=session,
    )


def _sent_params(session: Any) -> dict[str, Any]:
    return session.get.call_args.kwargs["params"]


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


def test_queue_listing_asks_for_live_totals(
    queues_service: QueuesService,
    session: Any,
):
    """The flags are the whole fix, so a silently dropped one must fail a test.

    Without them the management API answers from its statistics database, refreshed only
    every collect_statistics_interval (10s). Those depths lag, and not conservatively: a
    queue filled a moment ago still reads as empty, which made is_idle() report an idle
    system while the workers were saturated. Both flags are required —
    enable_queue_totals only takes effect once stats are disabled.
    """
    session.get.return_value.json.return_value = []

    queues_service.get_all_queue_message_counts()

    params = _sent_params(session)
    assert params["disable_stats"] == "true"
    assert params["enable_queue_totals"] == "true"


def test_single_queue_count_asks_for_live_totals(
    queues_service: QueuesService,
    session: Any,
):
    session.get.return_value.json.return_value = {"messages": 7}

    assert queues_service.get_message_count(queue_name=_QUEUE) == 7

    params = _sent_params(session)
    assert params["disable_stats"] == "true"
    assert params["enable_queue_totals"] == "true"


def test_queue_listing_counts_total_messages_not_just_ready(
    queues_service: QueuesService,
    session: Any,
):
    """``messages`` is ready + unacknowledged, and both halves matter.

    With task_acks_late=True a running task holds an unacked message and nothing else,
    so a ready-only count would read zero for a fully saturated worker.
    """
    session.get.return_value.json.return_value = [
        {"name": _LOOM_QUEUE, "messages": 5, "messages_ready": 2},
    ]

    assert queues_service.get_all_queue_message_counts() == {_LOOM_QUEUE: 5}


def test_queue_listing_separates_loom_and_delayed_queues(
    queues_service: QueuesService,
    session: Any,
):
    session.get.return_value.json.return_value = [
        {"name": _LOOM_QUEUE, "messages": 3},
        {"name": _DELAYED_QUEUE, "messages": 1},
    ]

    assert queues_service.get_all_queue_message_counts() == {_LOOM_QUEUE: 3}
    assert queues_service.get_delayed_queue_message_counts() == {_DELAYED_QUEUE: 1}


def test_queue_samples_still_read_the_statistics_database(
    queues_service: QueuesService,
    session: Any,
):
    """Historical rate samples exist only in the stats database.

    A live total answers "how deep is this queue now", never "how deep was it a minute
    ago", so this one method must keep its stats-backed request.
    """
    session.get.return_value.json.return_value = {
        "queue_totals": {"messages_details": {"samples": []}}
    }

    queues_service.get_queue_samples(sample_period__s=60)

    params = _sent_params(session)
    assert "disable_stats" not in params
    assert "enable_queue_totals" not in params
