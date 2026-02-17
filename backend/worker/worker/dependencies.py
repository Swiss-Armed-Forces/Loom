import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import DependencyException, get_celery_app
from gotenberg_client import GotenbergClient

from worker.services.rspamd_service import RspamdService
from worker.services.tika_service import TikaService
from worker.settings import settings

_tika_service: TikaService | None = None
_rspamd_service: RspamdService | None = None
_gotenberg_client: GotenbergClient | None = None


logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes worker dependencies")

    # init celery for package
    app = get_celery_app()
    register_tasks_for_package(app=app, package="worker")

    global _tika_service
    _tika_service = TikaService(common_dependencies.get_lazybytes_service())

    global _rspamd_service
    _rspamd_service = RspamdService(settings.rspam_host)

    global _gotenberg_client
    _gotenberg_client = GotenbergClient(
        str(settings.gotenberg_host), timeout=settings.gotenberg_timeout
    )


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()
    global _tika_service
    _tika_service = MagicMock(spec=TikaService)

    global _rspamd_service
    _rspamd_service = MagicMock(spec=RspamdService)

    global _gotenberg_client
    _gotenberg_client = MagicMock(spec=GotenbergClient)


def get_tika_service() -> TikaService:
    if _tika_service is None:
        raise DependencyException("Tika Service missing")
    return _tika_service


def get_rspamd_service() -> RspamdService:
    if _rspamd_service is None:
        raise DependencyException("Rspamd Service missing")
    return _rspamd_service


def get_gotenberg_client() -> GotenbergClient:
    if _gotenberg_client is None:
        raise DependencyException("Gotenberg Client missing")
    return _gotenberg_client
