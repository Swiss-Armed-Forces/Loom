import pytest
from common.celery_app import TaskGroupName
from common.dependencies import get_celery_inspect_service, get_redis_client
from common.services.celery_inspect_service import _TASK_GROUP_KEY_PREFIX

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

_TEST_TASK_NAME = "integration.test.task"
_TEST_TASK_NAMES_IN_GROUP = ("task.a", "task.b")
_TEST_GROUP = TaskGroupName.ALL


@pytest.fixture(autouse=True)
def clean_state():
    yield
    service = get_celery_inspect_service()
    service.set_throttled(False)
    service.set_task_paused(_TEST_TASK_NAME, False)
    get_redis_client().srem(
        f"{_TASK_GROUP_KEY_PREFIX}:{_TEST_GROUP.value}", *_TEST_TASK_NAMES_IN_GROUP
    )


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
    for task_name in _TEST_TASK_NAMES_IN_GROUP:
        service.register_task_in_group(_TEST_GROUP, task_name)
    assert set(_TEST_TASK_NAMES_IN_GROUP).issubset(
        set(service.get_task_names_in_group(_TEST_GROUP))
    )
