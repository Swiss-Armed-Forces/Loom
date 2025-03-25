from typing import Dict, Union
from urllib.parse import quote

import requests
from requests import Response

RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT = 30  # in seconds

# All application relevant queues must start with: "celery."
# And by default do not include queues with: "__", those are private queues.
QUEUES_NAME_REGEX = r"^celery(\.[a-zA-Z0-9]+)?$"


class QueuesService:
    def __init__(self, rabbit_mq_management_host: str):
        self.__rabbit_mq_management_host = rabbit_mq_management_host

    def get_message_count(
        self,
        queue_name: str | None = None,
    ) -> int:
        params: Dict[str, Union[int, str]]
        if queue_name is None:
            api_endpoint = "api/overview"
            params = {
                "columns": "queue_totals.messages",
                "name": quote(QUEUES_NAME_REGEX, safe=""),
                "use_regex": "true",
            }
        else:
            api_endpoint = (
                f"api/queues/{quote('/', safe='')}/{quote(queue_name, safe='')}"
            )
            params = {
                "columns": "messages",
            }
        response: Response = requests.get(
            self.__rabbit_mq_management_host + api_endpoint,
            params=params,
            timeout=RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        queue = response.json()

        if queue_name is None:
            queue = queue["queue_totals"]

        return int(queue["messages"])

    def get_queue_samples(
        self,
        sample_period__s: int,
        sample_count: int = 100,
        queue_name: str | None = None,
    ) -> list[tuple[int, int]]:
        params: Dict[str, Union[int, str]]
        if queue_name is None:
            api_endpoint = "api/overview"
            params = {
                "columns": "queue_totals.messages_details.samples",
                "name": quote(QUEUES_NAME_REGEX, safe=""),
                "use_regex": "true",
            }
        else:
            api_endpoint = (
                f"api/queues/{quote('/', safe='')}/{quote(queue_name, safe='')}"
            )
            params = {
                "columns": "messages_details.samples",
            }
        params = {
            **params,
            **{
                "lengths_age": sample_period__s,
                "lengths_incr": max(1, int(sample_period__s / sample_count)),
            },
        }
        response: Response = requests.get(
            self.__rabbit_mq_management_host + api_endpoint,
            params=params,
            timeout=RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        queue = response.json()

        if queue_name is None:
            queue = queue["queue_totals"]

        samples = []
        for sample in queue["messages_details"]["samples"]:
            timestamp = (
                sample["timestamp"] / 1000
            )  # convert millis timestamp to seconds
            value = sample["sample"]
            samples.append((timestamp, value))

        samples_sorted = (
            sorted(  # sort by timestamp ASCENDING -> NOW at the end of the list
                samples,
                key=lambda s: s[0],
            )
        )

        return samples_sorted
