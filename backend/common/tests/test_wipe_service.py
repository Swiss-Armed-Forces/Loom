# pylint: disable=redefined-outer-name
from typing import Any
from unittest.mock import MagicMock

import pytest

from common.services.celery_inspect_service import CeleryInspectService
from common.services.queues_service import QueuesService
from common.services.wipe_service import WipeService, WipeTimeoutError

LOOM_QUEUE = "loom:worker.index_file.dispatch_tasks.dispatch_index_file"
DELAYED_QUEUE = "celery_delayed_27"
EMPTY_QUEUE = "loom:abyss"


@pytest.fixture()
def queues_service() -> Any:
    service = MagicMock(spec=QueuesService)
    service.get_all_queue_message_counts.return_value = {LOOM_QUEUE: 3, EMPTY_QUEUE: 0}
    service.get_delayed_queue_message_counts.return_value = {DELAYED_QUEUE: 1}
    service.get_message_count.return_value = 4
    return service


@pytest.fixture()
def celery_inspect_service() -> Any:
    service = MagicMock(spec=CeleryInspectService)
    service.iterate_tasks.return_value = iter([])
    service.is_idle.return_value = True
    return service


@pytest.fixture()
def celery_app() -> Any:
    return MagicMock()


@pytest.fixture()
def wipe_service(
    celery_app: Any,
    queues_service: Any,
    celery_inspect_service: Any,
) -> WipeService:
    return WipeService(
        celery_app=celery_app,
        elasticsearch=MagicMock(),
        query_builder=MagicMock(),
        pubsub_service=MagicMock(),
        redis_client=MagicMock(),
        redis_cache_client=MagicMock(),
        s3_intake_client=MagicMock(),
        file_storage_service=MagicMock(),
        lazybytes_service=MagicMock(),
        imap_service=MagicMock(),
        celery_inspect_service=celery_inspect_service,
        queues_service=queues_service,
    )


def _purged(queues_service: Any) -> list[str]:
    return [call.args[0] for call in queues_service.purge_queue.call_args_list]


def test_wipe_rabbit_purges_queues_named_by_the_broker(
    wipe_service: WipeService,
    celery_app: Any,
    queues_service: Any,
):
    """The queue list must come from the broker, never from local Celery state.

    celery_control.purge() reaches only app.amqp.queues.consume_from, which excludes
    every per-task queue in processes that never call register_tasks_for_package() —
    i.e. the API, which has no 'worker' package installed.
    """
    wipe_service.wipe_rabbit()

    assert LOOM_QUEUE in _purged(queues_service)
    celery_app.control.purge.assert_not_called()


def test_wipe_rabbit_purges_delayed_retry_queues(
    wipe_service: WipeService,
    queues_service: Any,
):
    """is_idle() counts celery_delayed_* queues, so the purge must reach them too.

    Otherwise a task in a retry backoff keeps the system permanently non-idle.
    """
    wipe_service.wipe_rabbit()

    assert DELAYED_QUEUE in _purged(queues_service)


def test_wipe_rabbit_purges_queues_the_broker_reports_as_empty(
    wipe_service: WipeService,
    queues_service: Any,
):
    """A reported depth of 0 must not be trusted to mean the queue is empty.

    The management API serves depths from a stats database refreshed every 10s, and
    omits the messages column entirely for a queue it has not sampled yet. Skipping
    those queues let a wipe issued right after a burst of publishes return having purged
    nothing.
    """
    wipe_service.wipe_rabbit()

    assert EMPTY_QUEUE in _purged(queues_service)


def test_wipe_rabbit_purges_nothing_when_the_broker_names_no_queues(
    wipe_service: WipeService,
    queues_service: Any,
):
    queues_service.get_all_queue_message_counts.return_value = {}
    queues_service.get_delayed_queue_message_counts.return_value = {}

    wipe_service.wipe_rabbit()

    queues_service.purge_queue.assert_not_called()


def test_wipe_rabbit_propagates_a_failed_purge(
    wipe_service: WipeService,
    queues_service: Any,
):
    """Purges run concurrently, so their failures must be collected, not dropped."""
    queues_service.purge_queue.side_effect = RuntimeError("broker said no")

    with pytest.raises(RuntimeError, match="broker said no"):
        wipe_service.wipe_rabbit()


def test_wipe_celery_terminates_remaining_tasks_and_repurges_until_idle(
    wipe_service: WipeService,
    celery_app: Any,
    queues_service: Any,
    celery_inspect_service: Any,
):
    celery_inspect_service.iterate_tasks.side_effect = [
        iter([{"id": "task-1"}, {"id": "task-2"}]),
        iter([]),
    ]
    celery_inspect_service.is_idle.side_effect = [False, True]

    wipe_service.wipe_celery()

    terminated = [call.args[0] for call in celery_app.control.terminate.call_args_list]
    assert terminated == ["task-1", "task-2"]
    # Two iterations, each purging all three queues the broker named: tasks still in
    # flight publish successors as they complete, so purging only once would leave
    # those behind.
    assert queues_service.purge_queue.call_count == 6


def test_wipe_celery_raises_when_it_cannot_reach_idle(
    wipe_service: WipeService,
    celery_inspect_service: Any,
):
    """A wipe that gives up silently is worse than one that fails visibly."""
    celery_inspect_service.is_idle.return_value = False

    with pytest.raises(WipeTimeoutError, match="4 messages remain"):
        wipe_service.wipe_celery(timeout__s=0)
