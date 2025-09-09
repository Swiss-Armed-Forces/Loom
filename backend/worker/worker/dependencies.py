import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import DependencyException, get_celery_app

from worker.services.tika_service import TikaService

_tika_service: TikaService | None = None


logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes worker dependencies")

    # init celery for package
    app = get_celery_app()
    register_tasks_for_package(app=app, package="worker")

    global _tika_service
    _tika_service = TikaService(common_dependencies.get_lazybytes_service())


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()
    global _tika_service
    _tika_service = MagicMock(spec=TikaService)


def get_tika_service() -> TikaService:
    if _tika_service is None:
        raise DependencyException("Tika Service missing")
    return _tika_service
