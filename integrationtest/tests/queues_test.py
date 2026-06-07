import re

import pytest
import requests
from api.models.queues_model import CompleteEstimate, OverallQueuesStats
from common.dependencies import get_celery_app
from common.services.queues_service import QUEUES_NAME_REGEX
from kombu import Queue

from utils.consts import QUEUES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets


def _is_default_queue(queue: Queue) -> bool:
    return re.match(QUEUES_NAME_REGEX, queue.name) is not None


def _get_overall_queue_stats() -> OverallQueuesStats:
    response = requests.get(
        f"{QUEUES_ENDPOINT}/",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    return OverallQueuesStats.model_validate(response.json())


def _get_complete_estimate(queue: Queue) -> CompleteEstimate | None:
    response = requests.get(
        f"{QUEUES_ENDPOINT}/{queue.name}/complete_estimate",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    response_json = response.json()
    if response_json is None:
        return response_json
    return CompleteEstimate.model_validate(response_json)


def _get_message_count(queue: Queue) -> int:
    response = requests.get(
        f"{QUEUES_ENDPOINT}/{queue.name}/message_count",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    return int(response.json())


class TestQueues:

    asset_list = ["empty_file.txt"]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # ensure all files are processed
        fetch_files_from_api(
            search_string="*",
            expected_no_of_files=len(self.asset_list),
            wait_for_celery_idle=True,
        )

    def test_get_overall_queue_stats(self):
        # should be idle now
        queue_stats = _get_overall_queue_stats()
        assert queue_stats.complete_estimate_timestamp is None
        assert queue_stats.messages_in_queues == 0

    def test_get_complete_estimate(self):
        app = get_celery_app()

        # all queues should be idle now
        for queue in app.conf.task_queues:
            if _is_default_queue(queue):
                complete_estimate = _get_complete_estimate(queue)
                assert complete_estimate is None

    def test_get_messages(self):
        app = get_celery_app()

        # all queues should be idle now
        queue: Queue
        for queue in app.conf.task_queues:
            if _is_default_queue(queue):
                message_count = _get_message_count(queue)
                assert message_count == 0
