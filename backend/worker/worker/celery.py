"""Provides the worker entry point."""

import logging

from common.dependencies import get_celery_app, init

from worker.utils.patch_group import patch_group

logger = logging.getLogger(__name__)
init()
app = get_celery_app()
patch_group(app)

app.conf.update(
    include=["worker.tasks"],
)
