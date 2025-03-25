import asyncio
import json
import logging

import pytest
import requests
import websockets
from common.messages.messages import (
    MessageError,
    MessageFileUpdate,
    MessageSubscribConfirmation,
    MessageSubscribe,
    PubSubMessage,
)

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT, WEBSOCKET_ENDPOINT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_by_name,
)
from utils.upload_asset import upload_asset, upload_many_assets

logger = logging.getLogger(__name__)


def _add_tag(file_id: str, tag: str):
    response = requests.post(
        f"{FILES_ENDPOINT}/{file_id}/tags/{tag}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


async def _subscribe_to_channel(
    websocket: websockets.WebSocketClientProtocol, channels: set[str]
):
    subscribe_message = PubSubMessage(message=MessageSubscribe(channels=channels))
    await websocket.send(subscribe_message.model_dump_json())

    websocket_message = json.loads(await websocket.recv())
    response = PubSubMessage.model_validate(websocket_message)
    assert isinstance(response.message, MessageSubscribConfirmation)
    assert response.message.channels == channels


async def _assert_file_updated_message(
    websocket: websockets.WebSocketClientProtocol, file_id: str
):

    websocket_message = json.loads(await websocket.recv())
    response = PubSubMessage.model_validate(websocket_message)
    assert isinstance(response.message, MessageFileUpdate)
    assert response.message.fileId == file_id


@pytest.mark.asyncio
@pytest.mark.timeout(DEFAULT_MAX_WAIT_TIME_PER_FILE * 1)
async def test_file_update_message_single_asset():
    asset = "text.txt"
    tag_to_add = "test"
    upload_asset(asset)

    file = get_file_by_name(asset)
    file_id = str(file.file_id)
    async with websockets.connect(WEBSOCKET_ENDPOINT) as websocket:
        await _subscribe_to_channel(websocket, {file_id})

        _add_tag(file_id, tag_to_add)

        await _assert_file_updated_message(websocket, file_id)


@pytest.mark.asyncio
@pytest.mark.timeout(DEFAULT_MAX_WAIT_TIME_PER_FILE * 2)
async def test_file_update_message_multiple_assets():
    assets = ["basic_email.eml", "text.txt"]
    tag_to_add = "test"
    upload_many_assets(assets)

    file_ids = set()
    files = fetch_files_from_api(expected_no_of_files=len(assets))
    for assets in files.files:
        file_ids.add(str(assets.file_id))
    async with websockets.connect(WEBSOCKET_ENDPOINT) as websocket:
        await _subscribe_to_channel(websocket, file_ids)

        for file_id in file_ids:
            _add_tag(file_id, tag_to_add)

        for _ in file_ids:
            websocket_message = await websocket.recv()
            response = PubSubMessage.model_validate(json.loads(websocket_message))
            assert isinstance(response.message, MessageFileUpdate)
            assert response.message.fileId in file_ids


@pytest.mark.asyncio
@pytest.mark.timeout(DEFAULT_MAX_WAIT_TIME_PER_FILE * 1)
async def test_file_update_message_multiple_connections():
    tag_to_add = "test"

    async def start_connection(file_id: str, barrier: asyncio.Barrier):
        async with websockets.connect(WEBSOCKET_ENDPOINT) as websocket:
            await _subscribe_to_channel(websocket, {file_id})

            # wait for all threads to connect
            async with barrier as position:
                if position == 0:
                    _add_tag(file_id, tag_to_add)

            websocket_message = await websocket.recv()
            response = PubSubMessage.model_validate(json.loads(websocket_message))
            assert isinstance(response.message, MessageFileUpdate)
            assert response.message.fileId == file_id

    asset = "text.txt"
    upload_asset(asset)

    file = get_file_by_name(asset)
    file_id = str(file.file_id)
    barrier = asyncio.Barrier(2)
    task_one = asyncio.create_task(start_connection(file_id, barrier))
    task_two = asyncio.create_task(start_connection(file_id, barrier))

    await task_one
    await task_two


@pytest.mark.asyncio
@pytest.mark.timeout(DEFAULT_MAX_WAIT_TIME_PER_FILE * 1)
async def test_message_invalid_json():
    async with websockets.connect(WEBSOCKET_ENDPOINT) as websocket:
        await websocket.send("}}}} this is a malformed JSON message")
        websocket_message = await websocket.recv()
        response = PubSubMessage.model_validate(json.loads(websocket_message))
        assert isinstance(response.message, MessageError)


@pytest.mark.asyncio
@pytest.mark.timeout(DEFAULT_MAX_WAIT_TIME_PER_FILE * 1)
async def test_message_invalid_message():
    async with websockets.connect(WEBSOCKET_ENDPOINT) as websocket:
        await websocket.send("this is not a message")
        websocket_message = await websocket.recv()
        response = PubSubMessage.model_validate(json.loads(websocket_message))
        assert isinstance(response.message, MessageError)
