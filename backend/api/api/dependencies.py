import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.dependencies import DependencyException

from api.services.agent_service import AgentService
from api.services.ai_service import AiService
from api.services.task_call_service import TaskCallService
from api.services.tool_service import ToolService
from api.services.websocket_service import WebsocketService

# Note, "= None" assignments are needed here to make flake8 happy
_websocket_service: WebsocketService | None = None
_task_call_service: TaskCallService | None = None
_tool_service: ToolService | None = None
_agent_service: AgentService | None = None
_ai_service: AiService | None = None

logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    common_dependencies.init()
    logger.info("Initializes api dependencies")

    global _websocket_service
    _websocket_service = WebsocketService(common_dependencies.get_pubsub_service())

    global _task_call_service
    _task_call_service = TaskCallService(
        common_dependencies.get_celery_app(),
        common_dependencies.get_root_task_information_repository(),
    )

    global _tool_service
    _tool_service = ToolService(_task_call_service)

    global _agent_service
    _agent_service = AgentService(get_tool_service())

    global _ai_service
    _ai_service = AiService(
        common_dependencies.get_ai_context_repository(),
        common_dependencies.get_task_scheduling_service(),
    )


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()

    global _websocket_service
    _websocket_service = MagicMock(spec=WebsocketService)

    global _task_call_service
    _task_call_service = MagicMock(spec=TaskCallService)

    global _tool_service
    _tool_service = MagicMock(spec=ToolService)

    global _agent_service
    _agent_service = MagicMock(spec=AgentService)

    global _ai_service
    _ai_service = MagicMock(spec=AiService)


def get_websocket_service() -> WebsocketService:
    if _websocket_service is None:
        raise DependencyException("Connection manager is missing")
    return _websocket_service


def get_task_call_service() -> TaskCallService:
    if _task_call_service is None:
        raise DependencyException("Task call service is missing")
    return _task_call_service


def get_tool_service() -> ToolService:
    if _tool_service is None:
        raise DependencyException("Tool service is missing")
    return _tool_service


def get_agent_service() -> AgentService:
    if _agent_service is None:
        raise DependencyException("Agent service is missing")
    return _agent_service


def get_ai_service() -> AiService:
    if _ai_service is None:
        raise DependencyException("AI service is missing")
    return _ai_service
