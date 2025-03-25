from datetime import datetime

from common.dependencies import get_queues_service
from fastapi.testclient import TestClient

from api.models.queues_model import OverallQueuesStats
from api.routers.queues import CompleteEstimate


def test_get_overall_queue_stats(client: TestClient):
    # setup mock
    now = datetime.now()
    queues_service_mock = get_queues_service()
    queues_service_mock.get_queue_samples.return_value = [
        (now.timestamp() + 0, 100),
        (now.timestamp() + 100, 90),
        # (now.timestamp() + 200, 80),
        (now.timestamp() + 300, 70),
        # (now.timestamp() + 400, 60),
        (now.timestamp() + 500, 50),
        # (now.timestamp() + 600, 40),
        # (now.timestamp() + 700, 30),
        # (now.timestamp() + 800, 20),
        # (now.timestamp() + 900, 10),
        # (now.timestamp() + 1000, 0),
    ]
    queues_service_mock.get_message_count.return_value = 50

    queue = "test_queue"
    queues_service_mock.task_queues_names = [queue]

    # do call
    response = client.get("/v1/queues/")
    response.raise_for_status()
    overall_queue_stats = OverallQueuesStats(**response.json())

    assert overall_queue_stats.messages_in_queues == 50
    assert overall_queue_stats.complete_estimate_timestamp == int(
        now.timestamp() + 1000
    )


def test_get_completed_estimate(client: TestClient):
    # setup mock
    now = datetime.now()
    queues_service_mock = get_queues_service()
    queues_service_mock.get_queue_samples.return_value = [
        (now.timestamp() + 0, 100),
        (now.timestamp() + 100, 90),
        # (now.timestamp() + 200, 80),
        (now.timestamp() + 300, 70),
        # (now.timestamp() + 400, 60),
        (now.timestamp() + 500, 50),
        # (now.timestamp() + 600, 40),
        # (now.timestamp() + 700, 30),
        # (now.timestamp() + 800, 20),
        # (now.timestamp() + 900, 10),
        # (now.timestamp() + 1000, 0),
    ]

    queue = "test_queue"
    queues_service_mock.task_queues_names = [queue]

    # do call
    response = client.get(f"/v1/queues/{queue}/complete_estimate")
    response.raise_for_status()
    complete_estimate = CompleteEstimate(**response.json())

    assert complete_estimate.samples_count == 4
    assert complete_estimate.estimate_timestamp == int(now.timestamp() + 1000)


def test_get_messages(client: TestClient):
    # setup mock
    queues_service_mock = get_queues_service()
    queues_service_mock.get_message_count.return_value = 100

    queue = "test_queue"
    queues_service_mock.task_queues_names = [queue]

    # do call
    response = client.get(f"/v1/queues/{queue}/message_count")
    response.raise_for_status()
    messages = int(response.json())

    assert messages == 100
