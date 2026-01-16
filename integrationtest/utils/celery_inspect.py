import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

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

    def count_total_tasks(worker_tasks: dict[str, list[Any]] | None):
        if worker_tasks is None:
            return 0
        return sum(len(tasks) for _, tasks in worker_tasks.items())

    inspect_methods = [inspect.active, inspect.scheduled, inspect.reserved]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(method, safe=True) for method in inspect_methods]
        return sum(count_total_tasks(f.result()) for f in futures)


def is_celery_idle() -> bool:
    celery_tasks_count = get_celery_tasks_count()
    messages_in_queues = get_messages_in_queues()

    return messages_in_queues <= 0 and celery_tasks_count <= 0
