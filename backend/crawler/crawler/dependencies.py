import logging
from unittest.mock import MagicMock

from common import dependencies as common_dependencies
from common.dependencies import DependencyException
from minio import Minio

from crawler.settings import settings

# Note, "= None" assignments are needed here to make flake8 happy
_s3_client: Minio | None = None

logger = logging.getLogger(__name__)


def init(subprocess_reinit: bool = False):
    # pylint: disable=global-statement
    logger.info(
        "Initializes crawler dependencies (subprocess_reinit=%s)", subprocess_reinit
    )

    global _s3_client
    _s3_client = Minio(
        settings.s3_host,
        secure=settings.s3_secure_connection,
    )


def mock_init():
    # pylint: disable=global-statement
    common_dependencies.mock_init()

    global _s3_client
    _s3_client = MagicMock(spec=Minio)


def get_s3_client() -> Minio:
    if _s3_client is None:
        raise DependencyException("S3 Client missing")
    return _s3_client
