import logging
from urllib.parse import urljoin

import requests
from pydantic import AnyHttpUrl

logger = logging.getLogger(__name__)

RSPAMD_TIMEOUT = 1200


class RspamdService:
    def __init__(self, host: AnyHttpUrl):
        self.host = host

    def detect_spam(self, data: memoryview | bytes) -> bool:
        symbols_api_endpoint = AnyHttpUrl(urljoin(str(self.host), "symbols"))
        response = requests.post(
            str(symbols_api_endpoint), data, timeout=RSPAMD_TIMEOUT
        )
        response.raise_for_status()
        json_response = response.json()
        return bool(json_response["default"]["is_spam"])
