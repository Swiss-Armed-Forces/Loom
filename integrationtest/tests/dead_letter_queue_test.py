import logging

import pytest
from common.celery_app import DeadTask
from common.dependencies import get_celery_app

logger = logging.getLogger(__name__)

GET_TIMEOUT = 180


def test_dead_letter_tasks():
    with pytest.raises(DeadTask):
        get_celery_app().send_task(
            "worker.test.sigkill_pgroup_task.sigkill_pgroup_task"
        ).get(timeout=GET_TIMEOUT)
