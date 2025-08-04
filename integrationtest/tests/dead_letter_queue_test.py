import logging
from time import sleep

import pytest
import requests

from utils.celery_inspect import is_celery_idle
from utils.consts import REQUEST_TIMEOUT, TESTS_ENDPOINT

logger = logging.getLogger(__name__)


@pytest.mark.timeout(30)
def test_dead_letter_tasks():
    response = requests.post(
        f"{TESTS_ENDPOINT}/dispatch_sigkill_pgroup_task", timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()

    # This polling-wait does not work in most cases
    # as the task scheduled form the previous api call
    # does not cause the queue/celery to be busy.
    #
    # Same issues as:
    #  - https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/25
    #
    # But we keep this test here anyways - logically the test is correct.
    while not is_celery_idle():
        logger.debug("Celery not idle yet")
        sleep(0.1)
