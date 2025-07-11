import logging
import os
import signal

from common.dependencies import get_celery_app

from worker.test.infra.test_task import TestTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=TestTask)
def sigkill_pgroup_task(*_, **__):
    """This task simulates a worker crash."""
    logger.info("Sending sigkill to pgroup")
    os.killpg(os.getpgrp(), signal.SIGKILL)
