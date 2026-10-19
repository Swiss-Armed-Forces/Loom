import pytest
from common.dependencies import get_queues_service
from common.settings import settings

# Every depth assertion below reads the broker a moment after `wipe_data` emptied
# it, and beat fires `compute-complete-estimate` and `beat-healthcheck` every
# minute -- so a test that happens to run on the minute sees one message and
# cannot tell it from a queue that never drained. Paused for the whole module
# rather than asserted around, which is what CLAUDE.md prescribes for a test that
# inspects queue depths.
pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")


@pytest.fixture(autouse=True)
def resume_all_queues_after_test():
    yield
    service = get_queues_service()
    for queue in service.get_paused_queues():
        service.set_queue_paused(queue, False)


def test_get_message_count_total_is_zero_when_idle():
    service = get_queues_service()
    # The per-queue breakdown as the message: a bare `1 == 0` says a queue is not
    # empty and not which, and the delayed queues are in the total but not in the
    # map, so their absence here is the answer too.
    assert service.get_message_count() == 0, service.get_all_queue_message_counts()


def test_get_message_count_per_queue_is_zero_when_idle():
    service = get_queues_service()
    for queue_name in service.get_all_queue_message_counts():
        assert service.get_message_count(queue_name=queue_name) == 0, queue_name


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


def test_get_queue_samples_total_returns_list():
    samples = get_queues_service().get_queue_samples(sample_period__s=60)
    assert isinstance(samples, list)


def test_get_queue_samples_total_is_sorted_ascending():
    samples = get_queues_service().get_queue_samples(sample_period__s=60)
    timestamps = [ts for ts, _ in samples]
    assert timestamps == sorted(timestamps)


def test_get_queue_samples_per_queue_returns_list():
    service = get_queues_service()
    queue_name = next(iter(service.get_all_queue_message_counts()))
    samples = service.get_queue_samples(sample_period__s=60, queue_name=queue_name)
    assert isinstance(samples, list)


def test_get_queue_samples_per_queue_is_sorted_ascending():
    service = get_queues_service()
    queue_name = next(iter(service.get_all_queue_message_counts()))
    samples = service.get_queue_samples(sample_period__s=60, queue_name=queue_name)
    timestamps = [ts for ts, _ in samples]
    assert timestamps == sorted(timestamps)


def test_set_queue_paused_and_is_queue_paused():
    service = get_queues_service()
    queue = "integration-test-queue"

    assert service.is_queue_paused(queue) is False

    service.set_queue_paused(queue, True)
    assert service.is_queue_paused(queue) is True

    service.set_queue_paused(queue, False)
    assert service.is_queue_paused(queue) is False


def test_get_paused_queues_reflects_pause_state():
    service = get_queues_service()
    queue = "integration-test-queue"

    assert queue not in service.get_paused_queues()

    service.set_queue_paused(queue, True)
    assert queue in service.get_paused_queues()

    service.set_queue_paused(queue, False)
    assert queue not in service.get_paused_queues()
