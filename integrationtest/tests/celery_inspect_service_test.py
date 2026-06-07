import pytest
from common.dependencies import get_celery_inspect_service, get_redis_client
from common.services.celery_inspect_service import _TASK_GROUP_KEY_PREFIX

_TEST_TASK_NAME = "integration.test.task"
_TEST_GROUP_NAME = "integration-test-group"


@pytest.fixture(autouse=True)
def clean_state():
    yield
    service = get_celery_inspect_service()
    service.set_throttled(False)
    service.set_task_paused(_TEST_TASK_NAME, False)
    get_redis_client().delete(f"{_TASK_GROUP_KEY_PREFIX}:{_TEST_GROUP_NAME}")


def test_count_tasks_is_zero_when_idle():
    assert get_celery_inspect_service().count_tasks() == 0


def test_wait_for_idle_returns_true_when_already_idle():
    assert get_celery_inspect_service().wait_for_idle(timeout=30) is True


def test_throttle_roundtrip():
    service = get_celery_inspect_service()
    assert service.is_throttled() is False
    service.set_throttled(True)
    assert service.is_throttled() is True
    service.set_throttled(False)
    assert service.is_throttled() is False


def test_set_task_paused_and_is_task_paused():
    service = get_celery_inspect_service()
    assert service.is_task_paused(_TEST_TASK_NAME) is False
    service.set_task_paused(_TEST_TASK_NAME, True)
    assert service.is_task_paused(_TEST_TASK_NAME) is True
    service.set_task_paused(_TEST_TASK_NAME, False)
    assert service.is_task_paused(_TEST_TASK_NAME) is False


def test_register_and_get_task_names_in_group():
    service = get_celery_inspect_service()
    assert service.get_task_names_in_group(_TEST_GROUP_NAME) == []
    service.register_task_in_group(_TEST_GROUP_NAME, "task.a")
    service.register_task_in_group(_TEST_GROUP_NAME, "task.b")
    assert set(service.get_task_names_in_group(_TEST_GROUP_NAME)) == {
        "task.a",
        "task.b",
    }
