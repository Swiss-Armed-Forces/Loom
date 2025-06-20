from unittest.mock import AsyncMock

from common.messages.messages import MessageNoop, PubSubMessage
from fastapi.testclient import TestClient

from api.dependencies import get_websocket_service

ENDPOINT = "/v1/websocket"


def test_get_websocket_messages(client: TestClient):
    message = PubSubMessage(message=MessageNoop())
    response = client.post(ENDPOINT, json=message.model_dump())
    assert response.raise_for_status()

    response_message = PubSubMessage.model_validate(response.json())
    assert message == response_message


def test_websocket_endpoint_connect_and_disconnect(client: TestClient):
    websocket_service = get_websocket_service()
    websocket_service.handle_websocket = AsyncMock()

    with client.websocket_connect(ENDPOINT) as websocket:
        websocket.close()

    websocket_service.handle_websocket.assert_awaited_once()
