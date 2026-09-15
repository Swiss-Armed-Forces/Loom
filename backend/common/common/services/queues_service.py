from typing import Dict, Union
from urllib.parse import quote

import requests
from redis import StrictRedis
from requests import Response

from common.settings import settings

RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT = 30  # in seconds

# All application relevant queues must start with: celery_queue_name_prefix
QUEUES_NAME_REGEX = rf"^{settings.celery_queue_name_prefix}.*$"

PAUSED_QUEUES_SET_KEY = "paused_queues_index"
CELERY_DELAYED_QUEUE_PREFIX = "celery_delayed"

# Query parameters that make the management API answer from the queue processes instead
# of its statistics database.
#
# By default /api/queues is served from the management stats database, which the broker
# refreshes only every collect_statistics_interval (10s, see
# charts/templates/rabbit/configMap.yaml). Depths read that way describe the broker as it
# was up to ten seconds ago — and the error is not conservative: a queue that has just
# been filled still reads as empty, which is how is_idle() came to report an idle system
# while the workers were saturated.
#
# With both flags set, rabbit_mgmt_wm_queues takes a different branch and calls
# rabbit_amqqueue:collect_info_all(..., totals, ...) — the same live query to the queue
# processes that `rabbitmqctl list_queues` performs. The totals cover ready *and*
# unacknowledged messages, which matters because task_acks_late=True means a running task
# holds an unacked message and nothing else.
#
# Both flags are required: enable_queue_totals only takes effect when stats are disabled.
LIVE_QUEUE_TOTALS_PARAMS: Dict[str, Union[int, str]] = {
    "disable_stats": "true",
    "enable_queue_totals": "true",
}


class QueuesService:
    """Queue depths and pause state.

    Every depth-reporting method here reads live totals from the queue processes (see
    ``LIVE_QUEUE_TOTALS_PARAMS``). The one exception is ``get_queue_samples()``, which
    serves historical rate samples: those exist only in the statistics database, so that
    method keeps reading it — correctly, since a point-in-time live total cannot answer
    what a queue looked like a minute ago.
    """

    def __init__(
        self,
        rabbit_mq_management_host: str,
        redis_client: StrictRedis,
        session: requests.Session | None = None,
    ):
        self.__rabbit_mq_management_host = rabbit_mq_management_host
        self._redis_client = redis_client
        # Injected so tests can assert on the requests without patching the module.
        # Also pools connections, which wipe_celery() leans on: it purges every queue on
        # every iteration, 16 requests at a time.
        self._session = session if session is not None else requests.Session()

    def set_queue_paused(self, queue_name: str, paused: bool) -> None:
        """Persist queue pause state in Redis."""
        if paused:
            self._redis_client.sadd(PAUSED_QUEUES_SET_KEY, queue_name)
        else:
            self._redis_client.srem(PAUSED_QUEUES_SET_KEY, queue_name)

    def is_queue_paused(self, queue_name: str) -> bool:
        """Check if a queue is currently paused according to Redis state."""
        return bool(self._redis_client.sismember(PAUSED_QUEUES_SET_KEY, queue_name))

    def get_paused_queues(self) -> list[str]:
        """Return all queue names that are currently paused in Redis."""
        return [
            member.decode()
            for member in self._redis_client.smembers(PAUSED_QUEUES_SET_KEY)
        ]

    def get_message_count(
        self,
        queue_name: str | None = None,
    ) -> int:
        if queue_name is None:
            return (
                sum(self.get_all_queue_message_counts().values())
                + self.get_delayed_queue_message_count()
            )
        api_endpoint = f"api/queues/{quote('/', safe='')}/{quote(queue_name, safe='')}"
        # No "columns" filter: disable_stats makes the server return the basic field set
        # regardless, so the parameter would only look like it still did something.
        response: Response = self._session.get(
            self.__rabbit_mq_management_host + api_endpoint,
            params=LIVE_QUEUE_TOTALS_PARAMS,
            timeout=RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return int(response.json()["messages"])

    def _get_queue_message_counts(self, prefix: str) -> dict[str, int]:
        """Return name -> message count for every queue whose name starts with
        prefix."""
        response: Response = self._session.get(
            self.__rabbit_mq_management_host + "api/queues/%2F",
            params=LIVE_QUEUE_TOTALS_PARAMS,
            timeout=RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return {
            q["name"]: int(q.get("messages", 0))
            for q in response.json()
            if q["name"].startswith(prefix)
        }

    def get_all_queue_message_counts(self) -> dict[str, int]:
        return self._get_queue_message_counts(settings.celery_queue_name_prefix)

    def get_delayed_queue_message_counts(self) -> dict[str, int]:
        """Return message counts for Celery's native delayed-delivery queues.

        These hold tasks in a ``retry(countdown=N)`` backoff. They do not carry the loom
        prefix, so ``get_all_queue_message_counts()`` never reports them — but
        ``CeleryInspectService.is_idle()`` does count them, so a wipe must be able to
        name and purge them or it can never reach idle.
        """
        return self._get_queue_message_counts(CELERY_DELAYED_QUEUE_PREFIX)

    def get_delayed_queue_message_count(self) -> int:
        return sum(self.get_delayed_queue_message_counts().values())

    def purge_queue(self, queue_name: str) -> None:
        response: Response = self._session.delete(
            self.__rabbit_mq_management_host
            + f"api/queues/{quote('/', safe='')}/{quote(queue_name, safe='')}/contents",
            timeout=RABBITMQ_MANAGEMENT_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

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
        response: Response = self._session.get(
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
