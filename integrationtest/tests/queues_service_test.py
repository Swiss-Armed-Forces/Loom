import re

from common.dependencies import get_celery_app, get_queues_service
from common.services.queues_service import QUEUES_NAME_REGEX
from common.settings import settings
from kombu import Queue


def _is_loom_queue(queue: Queue) -> bool:
    return re.match(QUEUES_NAME_REGEX, queue.name) is not None


# --- get_message_count (total) ---


def test_get_message_count_total_is_zero_when_idle():
    assert get_queues_service().get_message_count() == 0


# --- get_message_count (per queue) ---


def test_get_message_count_per_queue_is_zero_when_idle():
    service = get_queues_service()
    for queue in get_celery_app().conf.task_queues:
        if _is_loom_queue(queue):
            assert service.get_message_count(queue_name=queue.name) == 0


# --- get_all_queue_message_counts ---


def test_get_all_queue_message_counts_returns_dict():
    counts = get_queues_service().get_all_queue_message_counts()
    assert isinstance(counts, dict)


def test_get_all_queue_message_counts_keys_have_loom_prefix():
    counts = get_queues_service().get_all_queue_message_counts()
    prefix = settings.celery_queue_name_prefix
    for name in counts:
        assert name.startswith(prefix), f"Queue {name!r} does not start with {prefix!r}"


def test_get_all_queue_message_counts_all_zero_when_idle():
    counts = get_queues_service().get_all_queue_message_counts()
    for name, count in counts.items():
        assert count == 0, f"Queue {name!r} has {count} messages, expected 0"


# --- get_queue_samples ---


def test_get_queue_samples_total_returns_list():
    samples = get_queues_service().get_queue_samples(sample_period__s=60)
    assert isinstance(samples, list)


def test_get_queue_samples_total_is_sorted_ascending():
    samples = get_queues_service().get_queue_samples(sample_period__s=60)
    timestamps = [ts for ts, _ in samples]
    assert timestamps == sorted(timestamps)


def test_get_queue_samples_per_queue_returns_list():
    service = get_queues_service()
    for queue in get_celery_app().conf.task_queues:
        if _is_loom_queue(queue):
            samples = service.get_queue_samples(
                sample_period__s=60, queue_name=queue.name
            )
            assert isinstance(samples, list)
            break


def test_get_queue_samples_per_queue_is_sorted_ascending():
    service = get_queues_service()
    for queue in get_celery_app().conf.task_queues:
        if _is_loom_queue(queue):
            samples = service.get_queue_samples(
                sample_period__s=60, queue_name=queue.name
            )
            timestamps = [ts for ts, _ in samples]
            assert timestamps == sorted(timestamps)
            break


# --- get_consumer_count ---


def test_get_consumer_count_is_non_negative_for_each_loom_queue():
    service = get_queues_service()
    for queue in get_celery_app().conf.task_queues:
        if _is_loom_queue(queue):
            assert service.get_consumer_count(queue.name) >= 0


def test_get_consumer_count_is_positive_for_some_loom_queue():
    """At least one loom queue must have an active consumer when workers are running."""
    service = get_queues_service()
    counts = [
        service.get_consumer_count(queue.name)
        for queue in get_celery_app().conf.task_queues
        if _is_loom_queue(queue)
    ]
    assert any(
        c > 0 for c in counts
    ), "Expected at least one loom queue with a consumer"
