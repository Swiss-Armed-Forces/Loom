"""Test doubles for the S3 client, shared by everything that range-reads an object.

Written once because the interesting assertions are easy to leave out: that every
response was closed *and* released -- a leaked urllib3 connection is invisible until the
pool runs dry under load -- and that the bucket and object asked for were the ones
expected.

`backend/crawler/tests/test_archive_prescreen.py` keeps its own copy: the crawler
package cannot import from the common package's tests, and adding a path hook to a
conftest to make it possible would cost more than the duplication does.
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

from minio import Minio


class FakeResponse:
    """What minio's get_object hands back: a urllib3-ish response."""

    def __init__(self, payload: bytes):
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class ObjectStore:
    """Serves real byte ranges out of an in-memory object, and records the requests."""

    def __init__(self, payload: bytes, bucket: str, object_name: str):
        self.payload = payload
        self.bucket = bucket
        self.object_name = object_name
        self.responses: list[FakeResponse] = []

    def get_object(
        self, bucket: str, object_name: str, offset: int = 0, length: int = 0
    ) -> FakeResponse:
        assert bucket == self.bucket
        assert object_name == self.object_name
        end = offset + length if length else len(self.payload)
        response = FakeResponse(self.payload[offset:end])
        self.responses.append(response)
        return response

    @property
    def fetched_bytes(self) -> int:
        """How much was actually transferred, across every request."""
        return sum(len(response.read()) for response in self.responses)

    @property
    def every_response_was_released(self) -> bool:
        return bool(self.responses) and all(
            response.closed and response.released for response in self.responses
        )


@dataclass(frozen=True)
class S3Double:
    """A Minio double and the store behind it, which is what the assertions read."""

    client: MagicMock
    store: ObjectStore


def s3_serving(payload: bytes, bucket: str, object_name: str) -> S3Double:
    """A Minio double answering range requests out of `payload`."""
    store = ObjectStore(payload, bucket, object_name)
    client = MagicMock(spec=Minio)
    client.get_object.side_effect = store.get_object
    client.stat_object.return_value = MagicMock(size=len(payload))
    return S3Double(client=client, store=store)
