# pylint: disable=redefined-outer-name
import time
from typing import Any

import pytest

from common.celery_app import TaskGroupName
from common.dependencies import (
    get_celery_inspect_service,
    get_file_repository,
    get_queues_service,
    get_redis_client,
)
from common.services.complete_estimate_service import (
    _KEY_EMA_THROUGHPUT,
    _KEY_ESTIMATE_TS,
    _KEY_FILES_PENDING,
    _MIN_EMA_THROUGHPUT,
    CompleteEstimateService,
)
from common.services.query_builder import QueryParameters
from common.settings import settings


@pytest.fixture()
def service() -> CompleteEstimateService:
    return CompleteEstimateService(
        redis_client=get_redis_client(),
        queues_service=get_queues_service(),
        celery_inspect_service=get_celery_inspect_service(),
        file_repository=get_file_repository(),
    )


def test_get_pending_work_combines_dispatch_and_es(service: CompleteEstimateService):
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = ["worker.dispatch_task"]
    queues_service.get_all_queue_message_counts.return_value = {
        "loom:worker.dispatch_task": 5,
        "loom:worker.index_file_task": 10,
    }
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 3

    result = service._get_pending_work()  # pylint: disable=protected-access

    assert result == 8  # 5 dispatch + 3 ES
    celery_inspect.get_task_names_in_group.assert_called_once_with(
        TaskGroupName.DISPATCH.value
    )
    file_repository.count_by_query.assert_called_once_with(
        QueryParameters(
            query_id="pit-id",
            search_string=(
                f'NOT state:("processed" OR "failed")'
                f" AND reindex_count:<{settings.max_reindex_count}"
            ),
        )
    )


def test_compute_and_store_first_tick(service: CompleteEstimateService):
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 100

    # No previous state in Redis
    redis.pipeline.return_value.execute.return_value = [None, None, None]

    service.compute_and_store()

    # First tick: pending stored, no EMA yet, no estimate
    redis.set.assert_any_call(_KEY_FILES_PENDING, 100)
    redis.delete.assert_called_once_with(_KEY_ESTIMATE_TS)


def test_compute_and_store_second_tick_produces_estimate(
    service: CompleteEstimateService,
):
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 80  # was 100, now 80

    now = time.time()

    # Simulate previous tick: 100 pending, 60 seconds ago, no EMA yet
    redis.pipeline.return_value.execute.return_value = [
        b"100",
        str(now - 60).encode(),
        None,
    ]

    service.compute_and_store()

    # Throughput = (100 - 80) / 60 = 0.333 files/s, EMA = that value (first real EMA)
    # Estimate = now + 80 / 0.333 ≈ now + 240s
    redis.set.assert_any_call(_KEY_FILES_PENDING, 80)
    # EMA and estimate_ts should be set (not deleted)
    set_calls = {call.args[0] for call in redis.set.call_args_list}
    assert _KEY_EMA_THROUGHPUT in set_calls
    assert _KEY_ESTIMATE_TS in set_calls
    redis.delete.assert_not_called()


def test_compute_and_store_idle_clears_estimate_and_ema(
    service: CompleteEstimateService,
):
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 0  # all work done → idle

    now = time.time()

    redis.pipeline.return_value.execute.return_value = [
        b"10",
        str(now - 60).encode(),
        b"0.1",
    ]

    service.compute_and_store()

    # Both EMA and estimate_ts must be cleared when system goes idle
    deleted_keys = {call.args[0] for call in redis.delete.call_args_list}
    assert _KEY_EMA_THROUGHPUT in deleted_keys
    assert _KEY_ESTIMATE_TS in deleted_keys


def test_compute_and_store_negative_ema_clamped_to_zero(
    service: CompleteEstimateService,
):
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = (
        120  # more than before → negative rate
    )

    now = time.time()

    # Previous tick: 100 files, positive EMA
    redis.pipeline.return_value.execute.return_value = [
        b"100",
        str(now - 60).encode(),
        b"0.5",
    ]

    service.compute_and_store()

    # Negative rate blends into EMA; clamped value stored must be >= 0
    ema_set_calls = [
        call for call in redis.set.call_args_list if call.args[0] == _KEY_EMA_THROUGHPUT
    ]
    assert len(ema_set_calls) == 1
    stored_ema = ema_set_calls[0].args[1]
    assert stored_ema >= 0.0


def test_compute_and_store_near_zero_ema_suppresses_estimate(
    service: CompleteEstimateService,
):
    """EMA decayed to near-zero (e.g. after many stalled ticks) must not produce an
    estimate — dividing by a tiny EMA yields astronomically large timestamps."""
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 50  # still work remaining

    now = time.time()

    # Simulate an EMA that has decayed to just below the minimum threshold
    tiny_ema = _MIN_EMA_THROUGHPUT * 0.5
    redis.pipeline.return_value.execute.return_value = [
        b"50",  # last_pending == current → rate = 0 → EMA decays further
        str(now - 60).encode(),
        str(tiny_ema).encode(),
    ]

    service.compute_and_store()

    # estimate_ts must be deleted, not set
    deleted_keys = {call.args[0] for call in redis.delete.call_args_list}
    assert _KEY_ESTIMATE_TS in deleted_keys
    set_keys = {call.args[0] for call in redis.set.call_args_list}
    assert _KEY_ESTIMATE_TS not in set_keys


def test_get_cached_result_returns_values(service: CompleteEstimateService):
    redis: Any = get_redis_client()

    future_ts = int(time.time()) + 300  # 5 minutes in the future

    def redis_get_side_effect(key: str):
        if key == _KEY_ESTIMATE_TS:
            return str(future_ts).encode()
        if key == _KEY_FILES_PENDING:
            return b"42"
        return None

    redis.get.side_effect = redis_get_side_effect

    result = service.get_cached_result()

    assert result.estimate_timestamp == future_ts
    assert result.files_pending == 42


def test_get_cached_result_returns_none_when_empty(service: CompleteEstimateService):
    redis: Any = get_redis_client()
    redis.get.return_value = None

    result = service.get_cached_result()

    assert result.estimate_timestamp is None
    assert result.files_pending is None


def test_get_cached_result_returns_none_for_past_timestamp(
    service: CompleteEstimateService,
):
    redis: Any = get_redis_client()

    past_ts = int(time.time()) - 300  # 5 minutes in the past

    def redis_get_side_effect(key: str):
        if key == _KEY_ESTIMATE_TS:
            return str(past_ts).encode()
        if key == _KEY_FILES_PENDING:
            return b"10"
        return None

    redis.get.side_effect = redis_get_side_effect

    result = service.get_cached_result()

    assert result.estimate_timestamp is None
    assert result.files_pending == 10
