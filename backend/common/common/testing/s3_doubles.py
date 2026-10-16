"""Test doubles for the S3 client, shared by everything that range-reads an object.

Written once because the interesting assertions are easy to leave out: that every
response was closed *and* released -- a leaked urllib3 connection is invisible until the
pool runs dry under load -- and that the bucket and object asked for were the ones
expected.

Kept inside the `common` source tree rather than beside its tests so that the crawler,
worker and api suites can import it too; `backend/common/pyproject.toml` excludes this
package from the wheel, so nothing here ships to a pod.

The client double is a plain object typed against `S3ObjectClient` rather than a
`MagicMock(spec=Minio)`: a spec'd mock validates attribute *names* at runtime and
nothing at all statically, so a double whose `get_object` had drifted from the real
signature would go unnoticed by mypy and by every suite using it.
"""

from dataclasses import dataclass

from minio.error import S3Error

from common.services.s3_range_reader import S3ObjectClient


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


@dataclass(frozen=True)
class FakeStat:
    """What minio's stat_object hands back, as far as this code is concerned."""

    size: int | None


def _unsatisfiable_range(bucket_name: str, object_name: str, offset: int) -> S3Error:
    """The error real object storage answers a range starting at or past the end with.

    Reproduced rather than approximated by an empty read, because `fetch_range`'s clamp
    exists for precisely this: against SeaweedFS a zero-length object -- which the
    prescreen meets for real -- answers HTTP 416, and a double that returned b"" would
    let the clamp be deleted with every test still green.
    """
    return S3Error(
        response=None,  # type: ignore[arg-type]
        code="InvalidRange",
        message=f"The requested range is not satisfiable: bytes={offset}-",
        resource=f"/{bucket_name}/{object_name}",
        request_id=None,
        host_id=None,
        bucket_name=bucket_name,
        object_name=object_name,
    )


class ObjectStore:
    """Serves real byte ranges out of an in-memory object, and records the requests."""

    def __init__(self, payload: bytes, bucket: str, object_name: str):
        self.payload = payload
        self.bucket = bucket
        self.object_name = object_name
        self.responses: list[FakeResponse] = []

    def get_object(
        self, bucket_name: str, object_name: str, offset: int = 0, length: int = 0
    ) -> FakeResponse:
        assert bucket_name == self.bucket
        assert object_name == self.object_name
        if offset >= len(self.payload):
            raise _unsatisfiable_range(bucket_name, object_name, offset)
        end = offset + length if length else len(self.payload)
        response = FakeResponse(self.payload[offset:end])
        self.responses.append(response)
        return response

    def stat_object(self, bucket_name: str, object_name: str) -> FakeStat:
        assert bucket_name == self.bucket
        assert object_name == self.object_name
        return FakeStat(size=len(self.payload))

    @property
    def request_count(self) -> int:
        """How many range requests were served."""
        return len(self.responses)

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

    client: S3ObjectClient
    store: ObjectStore


def s3_serving(payload: bytes, bucket: str, object_name: str) -> S3Double:
    """A Minio double answering range requests out of `payload`."""
    store = ObjectStore(payload, bucket, object_name)
    return S3Double(client=store, store=store)
