import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.dependencies import DependencyException
from minio import Minio

from crawler.settings import settings

# Note, "= None" assignments are needed here to make flake8 happy
_minio_client: Minio | None = None

logger = logging.getLogger(__name__)


def init():
    # pylint: disable=global-statement
    logger.info("Initializes crawler dependencies")

    global _minio_client
    _minio_client = Minio(
        settings.minio_host,
        settings.minio_access_key,
        settings.minio_secret_key,
        secure=settings.minio_secure_connection,
    )


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()

    global _minio_client
    _minio_client = MagicMock(spec=Minio)


def get_minio_client() -> Minio:
    if _minio_client is None:
        raise DependencyException("MinIO Client missing")
    return _minio_client
