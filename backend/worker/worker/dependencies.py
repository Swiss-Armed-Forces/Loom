from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_queues_for_package
from common.dependencies import DependencyException
from ollama import Client

from worker.services.tika_service import TikaService
from worker.settings import settings
from worker.utils.patch_group import patch_group

_tika_service: TikaService | None = None

_ollama_client: Client | None = None


def init():
    # pylint: disable=global-statement

    # init celery with worker tasks
    app = common_dependencies.get_celery_app()
    patch_group(app=app)
    register_queues_for_package(app=app, package="worker")

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
