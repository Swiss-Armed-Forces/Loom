import logging

import requests
from api.models.queues_model import OverallQueuesStats
from common.dependencies import get_celery_app
from requests import Response

from utils.consts import QUEUES_ENDPOINT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def get_messages_in_queues() -> int:
    response: Response = requests.get(f"{QUEUES_ENDPOINT}/", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    queues = OverallQueuesStats.model_validate(response.json())
    return queues.messages_in_queues


def get_celery_tasks_count() -> int:
    inspect = get_celery_app().control.inspect()

    active_tasks_count = 0

    active_tasks = inspect.active()
    if active_tasks is not None:
        for active_worker_tasks in active_tasks.values():
            active_tasks_count += len(active_worker_tasks)

    scheduled_tasks = inspect.scheduled()
    if scheduled_tasks is not None:
        for scheduled_worker_tasks in scheduled_tasks.values():
            active_tasks_count += len(scheduled_worker_tasks)

    return active_tasks_count


def is_celery_idle() -> bool:
    celery_tasks_count = get_celery_tasks_count()
    messages_in_queues = get_messages_in_queues()

    return messages_in_queues <= 0 and celery_tasks_count <= 0
