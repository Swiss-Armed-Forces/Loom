import logging
from asyncio import create_task, gather
from json import JSONDecodeError
from traceback import format_exception

from fastapi import WebSocket
from pydantic import ValidationError

from common.messages.messages import MessageError, PubSubMessage
from common.messages.pubsub_service import PubSubService, _PubSubAsync

logger = logging.getLogger(__name__)


class WebsocketService:
    def __init__(self, pubsub_service: PubSubService):
        self._pubsub_service = pubsub_service

    async def _websocket_reader(self, websocket: WebSocket, pubsub: _PubSubAsync):
        while True:
            try:
                websocket_message = await websocket.receive_json()
            except JSONDecodeError as ex:
                await websocket.send_json(
                    PubSubMessage(
                        message=MessageError(message="".join(format_exception(ex)))
                    ).model_dump()
                )
                continue
            try:
                message = PubSubMessage.model_validate(websocket_message)
            except ValidationError as ex:
                await websocket.send_json(
                    PubSubMessage(
                        message=MessageError(message="".join(format_exception(ex)))
                    ).model_dump()
                )
                continue
            await pubsub.publish_message(message)

    async def _websocket_writer(self, websocket: WebSocket, pubsub: _PubSubAsync):
        while True:
            message = await pubsub.get_message()
            await websocket.send_text(message.model_dump_json())

    async def handle_websocket(self, websocket: WebSocket):
        async with self._pubsub_service.open_async() as pubsub:
            websocket_writer = create_task(self._websocket_writer(websocket, pubsub))
            websocket_reader = create_task(self._websocket_reader(websocket, pubsub))
            try:
                await gather(websocket_writer, websocket_reader)
            finally:
                websocket_writer.cancel()
                websocket_reader.cancel()
