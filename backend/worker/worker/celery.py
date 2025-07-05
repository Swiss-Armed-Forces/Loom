"""Provides the worker entry point."""

import logging
import sys

from celery import Celery
from common.celery_app import init_minimal_celery_app
from common.dependencies import get_celery_app
from common.dependencies import init as init_common_dependencies

from worker.dependencies import init

logger = logging.getLogger(__name__)

app: Celery
# Return a minimal celery app if we are running the inspect command.
# This is to facilitate lightweight running of inspect command.
if "inspect" in sys.argv:
    logger.info("Initializing minimal Celery app")
    app = init_minimal_celery_app()
else:
    logger.info("Initializing Celery app")
    init_common_dependencies()
    init()
    app = get_celery_app()
