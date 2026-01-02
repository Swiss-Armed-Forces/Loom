import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.celery_app import register_tasks_for_package
from common.dependencies import DependencyException, get_celery_app

from worker.services.imap_service import IMAPService
from worker.services.rspamd_service import RspamdService
from worker.services.tika_service import TikaService
from worker.settings import settings

_tika_service: TikaService | None = None
_imap_service: IMAPService | None = None
_rspamd_service: RspamdService | None = None


logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes worker dependencies")

    # init celery for package
    app = get_celery_app()
    register_tasks_for_package(app=app, package="worker")

    global _tika_service
    _tika_service = TikaService(common_dependencies.get_lazybytes_service())

    global _imap_service
    _imap_service = IMAPService(
        settings.imap_host, settings.imap_user, settings.imap_password
    )

    global _rspamd_service
    _rspamd_service = RspamdService(settings.rspam_host)


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()
    global _tika_service
    _tika_service = MagicMock(spec=TikaService)


def get_tika_service() -> TikaService:
    if _tika_service is None:
        raise DependencyException("Tika Service missing")
    return _tika_service


def get_imap_service() -> IMAPService:
    if _imap_service is None:
        raise DependencyException("IMAP Service missing")
    return _imap_service


def get_rspamd_service() -> RspamdService:
    if _rspamd_service is None:
        raise DependencyException("Rspamd Service missing")
    return _rspamd_service
