import logging

from common.messages.messages import PubSubMessage
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.dependencies import get_websocket_service
from api.services.websocket_service import WebsocketService

router = APIRouter()

logger = logging.getLogger(__name__)

default_websocket_service = Depends(get_websocket_service)


@router.post("")
def websocket_messages(message: PubSubMessage) -> PubSubMessage:
    return message


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    websocket_service: WebsocketService = default_websocket_service,
):
    await websocket.accept()
    try:
        await websocket_service.handle_websocket(websocket)
    except WebSocketDisconnect:
        logger.debug("Websocket disconnected: %s", websocket.client)
