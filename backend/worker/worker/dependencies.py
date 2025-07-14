import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import DependencyException, get_celery_app
from ollama import Client

from worker.services.tika_service import TikaService
from worker.settings import settings

_tika_service: TikaService | None = None

_ollama_client: Client | None = None

logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes worker dependencies")

    # init celery for package
    app = get_celery_app()
    register_tasks_for_package(app=app, package="worker")

    global _tika_service
    _tika_service = TikaService(common_dependencies.get_lazybytes_service())

    global _ollama_client
    _ollama_client = Client(str(settings.ollama_host), timeout=settings.llm_timeout)


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()
    global _tika_service
    _tika_service = MagicMock(spec=TikaService)

    global _ollama_client
    _ollama_client = MagicMock(spec=Client)


def get_tika_service() -> TikaService:
    if _tika_service is None:
        raise DependencyException("Tika Service missing")
    return _tika_service


def get_ollama_client() -> Client:
    if _ollama_client is None:
        raise DependencyException("Ollama Client missing")
    return _ollama_client
