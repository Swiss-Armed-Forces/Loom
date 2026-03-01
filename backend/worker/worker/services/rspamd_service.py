import logging
from itertools import chain
from typing import Generator, Iterable
from urllib.parse import urljoin

import requests
from pydantic import AnyHttpUrl

logger = logging.getLogger(__name__)

RSPAMD_TIMEOUT = 1200


class RspamdService:
    def __init__(self, host: AnyHttpUrl):
        self.host = host

    def _peek_and_chain(
        self, data_generator: Generator[bytes, None, None]
    ) -> Iterable[bytes] | None:
        """Peek at the first chunk of a generator and chain it back.

        Returns None if the generator is empty, otherwise returns an iterable with the
        first chunk chained back to the rest of the generator.
        """
        try:
            first_chunk = next(data_generator)
        except StopIteration:
            return None
        return chain([first_chunk], data_generator)

    def detect_spam_from_generator(
        self, data_generator: Generator[bytes, None, None]
    ) -> bool:
        """Detect spam by streaming file content to Rspamd."""
        data_iterable = self._peek_and_chain(data_generator)
        if data_iterable is None:
            return False

        symbols_api_endpoint = AnyHttpUrl(urljoin(str(self.host), "symbols"))
        response = requests.post(
            str(symbols_api_endpoint), data_iterable, timeout=RSPAMD_TIMEOUT
        )
        response.raise_for_status()
        json_response = response.json()
        return bool(json_response["default"]["is_spam"])
