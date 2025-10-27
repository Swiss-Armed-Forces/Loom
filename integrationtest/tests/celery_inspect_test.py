from utils.celery_inspect import get_celery_tasks_count, get_messages_in_queues


def test_get_messages_in_queues():
    assert get_messages_in_queues() == 0


def test_get_celery_tasks_count():
    assert get_celery_tasks_count() == 0
