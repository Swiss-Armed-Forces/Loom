from asyncio import Barrier, Future
from unittest.mock import AsyncMock

import pytest
from common.dependencies import get_pubsub_service
from common.messages.messages import MessageError, MessageNoop, PubSubMessage
from common.messages.pubsub_service import PubSubService, _PubSubAsync
from fastapi import WebSocket, WebSocketDisconnect

from api.services.websocket_service import WebsocketService


@pytest.fixture(name="pubsub_service_mocks")
def fixture_pubsub_service_mock() -> tuple[PubSubService, _PubSubAsync]:
    pubsub_service_mock = get_pubsub_service()
    pubsub_service_async_mock = AsyncMock(spec=_PubSubAsync)

    # link the two mocks
    pubsub_service_mock.open_async.return_value.__aenter__.return_value = (
        pubsub_service_async_mock
    )
    return pubsub_service_mock, pubsub_service_async_mock


@pytest.mark.asyncio
async def test_read_from_pubsub_service(
    pubsub_service_mocks: tuple[PubSubService, _PubSubAsync],
):
    pubsub_service_mock, pubsub_service_async_mock = pubsub_service_mocks

    barrier = Barrier(2)

    async def wait_forever():
        await barrier.wait()
        await Future()  # run forever

    async def wait_and_disconnect_websocket():
        await barrier.wait()
        raise WebSocketDisconnect()

    pubsub_service_async_mock.get_message.side_effect = wait_forever

    websocket_service = WebsocketService(pubsub_service=pubsub_service_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json.side_effect = wait_and_disconnect_websocket

    with pytest.raises(WebSocketDisconnect):
        await websocket_service.handle_websocket(websocket=websocket)


@pytest.mark.asyncio
async def test_read_websocket_message(
    pubsub_service_mocks: tuple[PubSubService, _PubSubAsync],
):
    pubsub_service_mock, pubsub_service_async_mock = pubsub_service_mocks

    barrier = Barrier(2)

    async def wait_forever():
        await barrier.wait()
        await Future()  # run forever

    expected_message = PubSubMessage(message=MessageNoop())
    wait_and_receive_message_calls = 0

    async def wait_and_receive_message():
        nonlocal wait_and_receive_message_calls
        wait_and_receive_message_calls += 1
        if wait_and_receive_message_calls == 1:
            await barrier.wait()
            return expected_message.model_dump()
        raise WebSocketDisconnect()

    pubsub_service_async_mock.get_message.side_effect = wait_forever

    websocket_service = WebsocketService(pubsub_service=pubsub_service_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json.side_effect = wait_and_receive_message

    with pytest.raises(WebSocketDisconnect):
        await websocket_service.handle_websocket(websocket=websocket)

    pubsub_service_async_mock.publish_message.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_read_websocket_malformed_message(
    pubsub_service_mocks: tuple[PubSubService, _PubSubAsync],
):
    pubsub_service_mock, pubsub_service_async_mock = pubsub_service_mocks

    barrier = Barrier(2)

    async def wait_forever():
        await barrier.wait()
        await Future()  # run forever

    malformed_message = "This is not a valid message"
    wait_and_receive_message_calls = 0

    async def wait_and_receive_message():
        nonlocal wait_and_receive_message_calls
        wait_and_receive_message_calls += 1
        if wait_and_receive_message_calls == 1:
            await barrier.wait()
            return malformed_message
        raise WebSocketDisconnect()

    pubsub_service_async_mock.get_message.side_effect = wait_forever

    websocket_service = WebsocketService(pubsub_service=pubsub_service_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json.side_effect = wait_and_receive_message

    with pytest.raises(WebSocketDisconnect):
        await websocket_service.handle_websocket(websocket=websocket)

    message = PubSubMessage.model_validate(websocket.send_json.call_args_list[0][0][0])
    assert isinstance(message.message, MessageError)


@pytest.mark.asyncio
async def test_write_websocket_message(
    pubsub_service_mocks: tuple[PubSubService, _PubSubAsync],
):
    pubsub_service_mock, pubsub_service_async_mock = pubsub_service_mocks

    barrier = Barrier(2)

    async def wait_and_except():
        await barrier.wait()
        raise WebSocketDisconnect()

    expected_message = PubSubMessage(message=MessageNoop())
    wait_and_receive_message_calls = 0

    async def wait_and_receive_message():
        nonlocal wait_and_receive_message_calls
        wait_and_receive_message_calls += 1
        if wait_and_receive_message_calls == 1:
            return expected_message
        await barrier.wait()

    pubsub_service_async_mock.get_message.side_effect = wait_and_receive_message

    websocket_service = WebsocketService(pubsub_service=pubsub_service_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json.side_effect = wait_and_except

    with pytest.raises(WebSocketDisconnect):
        await websocket_service.handle_websocket(websocket=websocket)

    websocket.send_text.assert_called_with(expected_message.model_dump_json())
