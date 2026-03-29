from unittest.mock import MagicMock

from common.dependencies import get_task_scheduling_service
from fastapi.testclient import TestClient


def test_trigger_scheduled_task(client: TestClient):
    # setup mock
    task_scheduling_service_mock = get_task_scheduling_service()
    task_scheduling_service_mock.trigger_scheduled_task = MagicMock()

    # Use a real schedule name from get_beat_schedule()
    response = client.post("/v1/beat/cleanup-on-idle")

    assert response.status_code == 204
    task_scheduling_service_mock.trigger_scheduled_task.assert_called_once_with(
        "cleanup-on-idle"
    )


def test_trigger_scheduled_task_not_found(client: TestClient):
    # setup mock - validation happens at Pydantic level before reaching the service,
    # so invalid schedule names return 422 (validation error), not 404
    response = client.post("/v1/beat/non-existent-schedule")

    assert response.status_code == 422
    assert "non-existent-schedule" in response.text
