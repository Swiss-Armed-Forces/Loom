# pylint: disable=redefined-outer-name
import time
from typing import Any

import pytest

from common.dependencies import (
    get_celery_inspect_service,
    get_file_repository,
    get_queues_service,
    get_redis_client,
)
from common.services.celery_inspect_service import TaskGroupName
from common.services.complete_estimate_service import (
    _KEY_EMA_THROUGHPUT,
    _KEY_ESTIMATE_TS,
    _KEY_FILES_PENDING,
    _KEY_LAST_TIMESTAMP,
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
    redis.get.return_value = None

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
    def redis_get_side_effect(key: str):
        if key == _KEY_FILES_PENDING:
            return b"100"
        if key == _KEY_LAST_TIMESTAMP:
            return str(now - 60).encode()
        if key == _KEY_EMA_THROUGHPUT:
            return None
        return None

    redis.get.side_effect = redis_get_side_effect

    service.compute_and_store()

    # Throughput = (100 - 80) / 60 = 0.333 files/s, EMA = that value (first real EMA)
    # Estimate = now + 80 / 0.333 ≈ now + 240s
    redis.set.assert_any_call(_KEY_FILES_PENDING, 80)
    # EMA and estimate_ts should be set (not deleted)
    set_calls = {call.args[0] for call in redis.set.call_args_list}
    assert _KEY_EMA_THROUGHPUT in set_calls
    assert _KEY_ESTIMATE_TS in set_calls
    redis.delete.assert_not_called()


def test_compute_and_store_no_progress_clears_estimate(
    service: CompleteEstimateService,
):
    redis: Any = get_redis_client()
    queues_service: Any = get_queues_service()
    celery_inspect: Any = get_celery_inspect_service()
    file_repository: Any = get_file_repository()

    celery_inspect.get_task_names_in_group.return_value = []
    queues_service.get_all_queue_message_counts.return_value = {}
    file_repository.open_point_in_time.return_value = "pit-id"
    file_repository.count_by_query.return_value = 100  # same as before → no progress

    now = time.time()

    def redis_get_side_effect(key: str):
        if key == _KEY_FILES_PENDING:
            return b"100"
        if key == _KEY_LAST_TIMESTAMP:
            return str(now - 60).encode()
        if key == _KEY_EMA_THROUGHPUT:
            return b"0.0"
        return None

    redis.get.side_effect = redis_get_side_effect

    service.compute_and_store()

    # EMA converges toward 0, estimate should be cleared
    redis.delete.assert_called_once_with(_KEY_ESTIMATE_TS)


def test_get_cached_result_returns_values(service: CompleteEstimateService):
    redis: Any = get_redis_client()

    def redis_get_side_effect(key: str):
        if key == _KEY_ESTIMATE_TS:
            return b"9999"
        if key == _KEY_FILES_PENDING:
            return b"42"
        return None

    redis.get.side_effect = redis_get_side_effect

    result = service.get_cached_result()

    assert result.estimate_timestamp == 9999
    assert result.files_pending == 42


def test_get_cached_result_returns_none_when_empty(service: CompleteEstimateService):
    redis: Any = get_redis_client()
    redis.get.return_value = None

    result = service.get_cached_result()

    assert result.estimate_timestamp is None
    assert result.files_pending is None
