# pylint: disable=redefined-outer-name
from typing import Any
from unittest.mock import MagicMock

import pytest
from celery import Task

from common.dependencies import get_celery_app, get_queues_service, get_redis_client
from common.services.celery_inspect_service import (
    CeleryInspectService,
    TaskGroupName,
    _task_groups,
    task_group,
)


@pytest.fixture()
def celery_inspect_service() -> CeleryInspectService:
    return CeleryInspectService(
        celery_app=get_celery_app(),
        queues_service=get_queues_service(),
        redis_client=get_redis_client(),
    )


def test_task_group_decorator_registers_task():
    _task_groups.clear()

    mock_task = MagicMock(spec=Task)
    mock_task.name = "some.task"

    result = task_group(TaskGroupName.DISPATCH)(mock_task)

    assert result is mock_task
    assert "some.task" in _task_groups[TaskGroupName.DISPATCH.value]

    _task_groups.clear()


def test_set_task_paused_pauses_queue_and_cancels_consumer(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    celery_app: Any = get_celery_app()

    celery_inspect_service.set_task_paused("my.task", True)

    queues_service.set_queue_paused.assert_called_once()
    call_args = queues_service.set_queue_paused.call_args
    assert call_args[0][0].endswith("my.task")
    assert call_args[0][1] is True
    celery_app.control.cancel_consumer.assert_called_once()


def test_set_task_paused_resumes_queue_and_adds_consumer(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    celery_app: Any = get_celery_app()

    celery_inspect_service.set_task_paused("my.task", False)

    queues_service.set_queue_paused.assert_called_once()
    call_args = queues_service.set_queue_paused.call_args
    assert call_args[0][0].endswith("my.task")
    assert call_args[0][1] is False
    celery_app.control.add_consumer.assert_called_once()


def test_is_task_paused_delegates_to_queues_service(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.is_queue_paused.return_value = True

    result = celery_inspect_service.is_task_paused("my.task")

    assert result is True
    queues_service.is_queue_paused.assert_called_once()
    assert queues_service.is_queue_paused.call_args[0][0].endswith("my.task")


def test_set_taskgroup_paused_pauses_all_tasks_in_group(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    celery_app: Any = get_celery_app()
    redis_client: Any = get_redis_client()
    redis_client.smembers.return_value = {b"group.task_a", b"group.task_b"}

    celery_inspect_service.set_taskgroup_paused(TaskGroupName.DISPATCH, True)

    assert queues_service.set_queue_paused.call_count == 2
    assert celery_app.control.cancel_consumer.call_count == 2


def test_is_taskgroup_paused_returns_true_when_all_tasks_paused(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.is_queue_paused.return_value = True
    redis_client: Any = get_redis_client()
    redis_client.smembers.return_value = {b"group.task"}

    result = celery_inspect_service.is_taskgroup_paused(TaskGroupName.DISPATCH)

    assert result is True


def test_is_taskgroup_paused_returns_false_when_empty_group(
    celery_inspect_service: CeleryInspectService,
):
    redis_client: Any = get_redis_client()
    redis_client.smembers.return_value = set()

    result = celery_inspect_service.is_taskgroup_paused(TaskGroupName.DISPATCH)

    assert result is False


def test_is_idle_returns_true_when_no_messages(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.get_all_queue_message_counts.return_value = {}

    assert celery_inspect_service.is_idle() is True


def test_is_idle_returns_false_when_messages_pending(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.get_all_queue_message_counts.return_value = {"loom:some.task": 1}

    assert celery_inspect_service.is_idle() is False


def test_is_idle_include_tasks_only_counts_included_queues(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    # PROCESSING queue has 0 messages, but a periodic task queue has 1
    queues_service.get_all_queue_message_counts.return_value = {
        "loom:worker.processing_task": 0,
        "loom:worker.periodic_task": 1,
    }

    assert (
        celery_inspect_service.is_idle(include_tasks=["worker.processing_task"]) is True
    )


def test_is_idle_include_tasks_returns_false_when_included_queue_has_messages(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.get_all_queue_message_counts.return_value = {
        "loom:worker.processing_task": 2,
        "loom:worker.periodic_task": 1,
    }

    assert (
        celery_inspect_service.is_idle(include_tasks=["worker.processing_task"])
        is False
    )


def test_is_idle_include_tasks_empty_list_is_always_idle(
    celery_inspect_service: CeleryInspectService,
):
    queues_service: Any = get_queues_service()
    queues_service.get_all_queue_message_counts.return_value = {
        "loom:worker.some_task": 99,
    }

    assert celery_inspect_service.is_idle(include_tasks=[]) is True


def test_register_task_groups_persists_to_redis(
    celery_inspect_service: CeleryInspectService,
):
    redis_client: Any = get_redis_client()
    _task_groups.clear()
    _task_groups[TaskGroupName.DISPATCH.value] = ["my.task"]

    try:
        celery_inspect_service.register_task_groups()
    finally:
        _task_groups.clear()

    redis_client.sadd.assert_called_once()
    call_args = redis_client.sadd.call_args[0]
    assert "dispatch" in call_args[0]
    assert call_args[1] == "my.task"
