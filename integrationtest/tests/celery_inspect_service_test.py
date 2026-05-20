from common.dependencies import get_celery_inspect_service


def test_count_messages_in_queues():
    assert get_celery_inspect_service().count_messages_in_queues() == 0


def test_get_celery_tasks_count():
    assert get_celery_inspect_service().count_tasks() == 0
