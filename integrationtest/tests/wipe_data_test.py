"""Tests for POST /v1/wipe-data.

These deliberately go through HTTP rather than calling WipeService in-process. The
distinction matters: the API pod has no 'worker' package installed, so its Celery app
registers only the four static queues (loom:default, :graveyard, :dead, :abyss) — every
per-task queue is invisible to it. A wipe implemented against local Celery state
silently misses them. Only the HTTP path exercises that.
"""

import pytest
import requests
from api.models.queues_model import QueuesStats
from common.celery_app import TaskGroupName
from common.dependencies import get_celery_inspect_service

from utils.consts import QUEUES_ENDPOINT, REQUEST_TIMEOUT, WIPE_DATA_ENDPOINT
from utils.polling import poll_until
from utils.upload_asset import upload_many_assets

# The wipe loops on is_idle(); beat tasks would keep adding messages and prevent it from
# ever settling.
pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

_ASSET_NAME = "empty_file.txt"
_BACKLOG_FILE_COUNT = 20
# The management API serves queue depths from its stats database, which RabbitMQ refreshes
# only every collect_statistics_interval (10s, see charts/templates/rabbit/configMap.yaml).
# A just-published backlog is therefore invisible for up to that long.
_BACKLOG_VISIBLE_TIMEOUT_S = 60


@pytest.fixture(autouse=True)
def dispatch_state():
    """Re-register task groups before, restore consumption after.

    Before: a full wipe runs wipe_redis(), which flushes the task group registry that
    set_throttled() reads to decide which queues to pause. conftest restores it only once
    per class, so with --random-order a preceding full-wipe test in this module would
    otherwise leave the registry empty and make throttling a silent no-op.

    After: components=celery does not run wipe_redis(), so a throttle set here persists.
    Integration tests run --exitfirst, so this must survive a hard failure.
    """
    inspect = get_celery_inspect_service()
    inspect.register_task_groups()
    yield
    inspect.set_throttled(False)


def _queue_stats() -> QueuesStats:
    response = requests.get(f"{QUEUES_ENDPOINT}/stats", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return QueuesStats.model_validate(response.json())


def _wipe(components: list[str] | None = None) -> requests.Response:
    params: dict[str, str | list[str]] = {"confirmation": "wipe"}
    if components is not None:
        params["components"] = components
    return requests.post(WIPE_DATA_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)


def test_wipe_celery_purges_per_task_queues_no_worker_is_draining():
    """Regression test for wipe_celery() purging from local Celery state.

    "Queues are empty afterwards" alone does not discriminate — the broken version also
    ends up empty, by waiting for the workers to drain the backlog rather than by
    purging. So consumption is stopped first: with DISPATCH throttled the messages sit
    in loom:worker.index_file.dispatch_tasks.* — per-task queues, outside the API's four
    — with no consumer. A wipe that cannot purge them can never reach idle either, so it
    exhausts its timeout and returns 504 instead of 200.
    """
    inspect = get_celery_inspect_service()
    inspect.set_throttled(True)
    # Guard against a vacuous pass: if the task group registry were empty, nothing would
    # actually be paused and the workers would simply drain the backlog.
    assert inspect.is_taskgroup_paused(TaskGroupName.DISPATCH)

    upload_many_assets(asset_names=[_ASSET_NAME] * _BACKLOG_FILE_COUNT)
    poll_until(
        fetch=_queue_stats,
        predicate=lambda stats: stats.messages_in_queues > 0,
        timeout=_BACKLOG_VISIBLE_TIMEOUT_S,
        description="an undrainable backlog",
    )

    response = _wipe(components=["celery"])

    assert response.status_code == 200, response.text
    assert _queue_stats().messages_in_queues == 0


def test_wipe_all_components_leaves_queues_empty():
    upload_many_assets(asset_names=[_ASSET_NAME] * _BACKLOG_FILE_COUNT)

    response = _wipe()

    assert response.status_code == 200, response.text
    assert _queue_stats().messages_in_queues == 0


def test_wipe_rejects_wrong_confirmation():
    response = requests.post(
        WIPE_DATA_ENDPOINT,
        params={"confirmation": "nope"},
        timeout=REQUEST_TIMEOUT,
    )

    assert response.status_code == 400
