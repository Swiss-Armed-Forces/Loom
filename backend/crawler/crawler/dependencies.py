import logging

from common import dependencies as common_dependencies

logger = logging.getLogger(__name__)


def init():
    common_dependencies.init()
    logger.info("Initialize crawler dependencies")


def mock_init():
    common_dependencies.mock_init()
