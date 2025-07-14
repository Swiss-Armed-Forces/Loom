import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.dependencies import DependencyException

from api.services.websocket_service import WebsocketService

_websocket_service: WebsocketService | None = None

logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes api dependencies")

    global _websocket_service
    _websocket_service = WebsocketService(common_dependencies.get_pubsub_service())


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()

    global _websocket_service
    _websocket_service = MagicMock(spec=WebsocketService)


def get_websocket_service() -> WebsocketService:
    if _websocket_service is None:
        raise DependencyException("Connection manager is missing")
    return _websocket_service
