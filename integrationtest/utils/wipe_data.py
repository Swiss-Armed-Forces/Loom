#!/usr/bin/env python3

import logging

import requests

from utils.consts import WIPE_DATA_ENDPOINT

logger = logging.getLogger(__name__)

# A wipe drains Celery, Elasticsearch, Redis, S3 and IMAP in one synchronous request and
# reports nothing until it is done. This must exceed WIPE_CELERY_TIMEOUT__S so the
# server's 504 wins the race — otherwise the caller sees an opaque client-side read
# timeout instead of a diagnostic naming how many messages were left behind.
WIPE_REQUEST_TIMEOUT__S = 600


def wipe_data():
    """Wipe all loom state via the API.

    Routed through the endpoint rather than calling WipeService in-process so that the
    API path — the one real deployments use — is the path the tests exercise.
    """
    response = requests.post(
        WIPE_DATA_ENDPOINT,
        params={"confirmation": "wipe"},
        timeout=WIPE_REQUEST_TIMEOUT__S,
    )
    response.raise_for_status()
    logger.info("Wipe completed via API: %s", response.status_code)


if __name__ == "__main__":
    wipe_data()
