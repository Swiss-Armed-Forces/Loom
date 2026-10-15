import logging
from contextlib import contextmanager
from itertools import chain
from typing import Generator, Iterable
from urllib.parse import urljoin

import requests
from pydantic import AnyHttpUrl
from requests import HTTPError, RequestException

logger = logging.getLogger(__name__)

RSPAMD_TIMEOUT = 1200

# Status codes on which rspamd reports that it understood the request and refused this
# particular message. Every attempt fails the same way.
RSPAMD_PERMANENT_STATUS_CODES = frozenset({400, 403, 404, 405, 413, 415})


class RspamdError(Exception):
    """Rspamd scan exception."""


class RspamdTransientError(RspamdError):
    """Rspamd failed in a way a later attempt may survive.

    A restarting or overloaded scanner. Only this type belongs in a task's
    ``autoretry_for``.
    """


class RspamdPermanentError(RspamdError):
    """Rspamd understood the request and refused this message."""


def classify_rspamd_http_error(exc: HTTPError) -> RspamdError:
    """Map an HTTP status from rspamd onto the transient/permanent split.

    An unrecognised status counts as transient, for the same reason as in
    ``tika_service``: a wasted retry budget is cheaper than a wrong answer.
    """
    status_code = exc.response.status_code if exc.response is not None else None
    if status_code in RSPAMD_PERMANENT_STATUS_CODES:
        return RspamdPermanentError(f"rspamd refused the message: HTTP {status_code}")
    return RspamdTransientError(f"rspamd call failed: HTTP {status_code}")


@contextmanager
def _as_rspamd_error() -> Generator[None, None, None]:
    """Translate everything the transport can raise into the RspamdError hierarchy."""
    try:
        yield
    except HTTPError as exc:
        raise classify_rspamd_http_error(exc) from exc
    except RequestException as exc:
        # Connect or read timeout, a body that is not the JSON the API promises, DNS
        # failure, reset peer. requests raises JSONDecodeError from this tree too.
        raise RspamdTransientError("rspamd request failed") from exc


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
        """Detect spam by streaming file content to Rspamd.

        Raises RspamdTransientError or RspamdPermanentError on failures.
        """
        data_iterable = self._peek_and_chain(data_generator)
        if data_iterable is None:
            return False

        symbols_api_endpoint = AnyHttpUrl(urljoin(str(self.host), "symbols"))
        with _as_rspamd_error():
            response = requests.post(
                str(symbols_api_endpoint), data_iterable, timeout=RSPAMD_TIMEOUT
            )
            response.raise_for_status()
            json_response = response.json()
        return bool(json_response["default"]["is_spam"])
