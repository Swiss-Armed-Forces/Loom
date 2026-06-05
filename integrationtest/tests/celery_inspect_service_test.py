import pytest
from common.dependencies import get_celery_inspect_service


@pytest.fixture(autouse=True)
def resume_all_queues_after_test():
    yield
    service = get_celery_inspect_service()
    for queue in service.get_paused_queues():
        service.set_queue_paused(queue, False)


def test_count_messages_in_queues():
    assert get_celery_inspect_service().count_messages_in_queues() == 0


def test_get_celery_tasks_count():
    assert get_celery_inspect_service().count_tasks() == 0


def test_wait_for_idle_returns_true_when_already_idle():
    assert get_celery_inspect_service().wait_for_idle(timeout=30) is True


def test_set_queue_paused_and_is_queue_paused():
    service = get_celery_inspect_service()
    queue = "integration-test-queue"

    assert service.is_queue_paused(queue) is False

    service.set_queue_paused(queue, True)
    assert service.is_queue_paused(queue) is True

    service.set_queue_paused(queue, False)
    assert service.is_queue_paused(queue) is False


def test_get_paused_queues_reflects_pause_state():
    service = get_celery_inspect_service()
    queue = "integration-test-queue"

    assert queue not in service.get_paused_queues()

    service.set_queue_paused(queue, True)
    assert queue in service.get_paused_queues()

    service.set_queue_paused(queue, False)
    assert queue not in service.get_paused_queues()
