from common.dependencies import get_queues_service
from fastapi.testclient import TestClient

from api.models.queues_model import QueuesStats


def test_get_all_queues(client: TestClient):
    queues_service_mock = get_queues_service()
    queues_service_mock.get_all_queue_message_counts.return_value = {
        "queue-a": 10,
        "queue-b": 5,
    }

    response = client.get("/v1/queues/")
    response.raise_for_status()

    assert response.json() == {"queue-a": 10, "queue-b": 5}


def test_get_overall_queue_stats(client: TestClient):
    queues_service_mock = get_queues_service()
    queues_service_mock.get_message_count.return_value = 50
    queues_service_mock.get_paused_queues.return_value = ["q1"]

    response = client.get("/v1/queues/stats")
    response.raise_for_status()
    stats = QueuesStats.model_validate(response.json())

    assert stats.messages_in_queues == 50
    assert stats.paused_queues == ["q1"]


def test_get_messages(client: TestClient):
    queues_service_mock = get_queues_service()
    queues_service_mock.get_message_count.return_value = 100

    queue = "test_queue"

    response = client.get(f"/v1/queues/{queue}/message_count")
    response.raise_for_status()

    assert int(response.json()) == 100


def test_list_paused_queues(client: TestClient):
    queues_service_mock = get_queues_service()
    queues_service_mock.get_paused_queues.return_value = ["queue-a", "queue-b"]

    response = client.get("/v1/queues/paused")
    response.raise_for_status()

    assert set(response.json()) == {"queue-a", "queue-b"}
