"""One pass of the poll loop, end to end against a fake bucket.

`test_s3_crawler_watermark.py` covers the ledger thoroughly and never enters the loop
itself, so the batching, the `as_completed` wiring and the backoff -- the three things
this MR changed about it -- had no coverage at all, and the memory behaviour the batch
bound exists for lives entirely in that region.
"""

import io
import json
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from common.archive.archive_detection import MANIFEST_FILENAME
from common.archive.archive_repository import Archive
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from common.services.query_builder import QueryParameters
from minio.datatypes import Object

from crawler.s3_crawler import S3Crawler

BUCKET = "loom-intake"
NOW = datetime(2026, 6, 7, 9, 0, 0, tzinfo=timezone.utc)
ARCHIVE_ROOT_DIR = "loom_archive_2026-06-07_09_14_40.812597"


def _loom_archive_bytes() -> bytes:
    manifest = Archive(
        query=QueryParameters(query_id="q", search_string="*"),
        created_at=datetime(2026, 6, 7, 9, 14, 40),
    ).model_dump_json()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(
            f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}", json.dumps(json.loads(manifest))
        )
        zip_file.writestr(f"{ARCHIVE_ROOT_DIR}/files/report.pdf", b"%PDF-1.7" * 64)
    return buffer.getvalue()


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._payload

    def stream(self, chunk_size: int) -> Iterator[bytes]:
        for start in range(0, len(self._payload), chunk_size):
            yield self._payload[start : start + chunk_size]

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


@dataclass
class _FakeBucket:
    """Just enough of a Minio client for one poll: a listing and ranged reads."""

    objects: dict[str, bytes]
    stamps: dict[str, datetime]
    unreadable: set[str] = field(default_factory=set)
    responses: list[_FakeResponse] = field(default_factory=list)

    def list_objects(self, bucket_name: str, recursive: bool = False) -> list[Object]:
        assert bucket_name == BUCKET
        assert recursive
        return [
            Object(
                bucket_name,
                name,
                last_modified=self.stamps[name],
                size=len(payload),
            )
            for name, payload in self.objects.items()
        ]

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
        offset: int = 0,
        length: int = 0,
    ) -> _FakeResponse:
        assert bucket_name == BUCKET
        if object_name in self.unreadable:
            raise OSError(f"{object_name} is gone")
        payload = self.objects[object_name]
        end = offset + length if length else len(payload)
        response = _FakeResponse(payload[offset:end])
        self.responses.append(response)
        return response


@dataclass(frozen=True)
class _Subject:
    crawler: S3Crawler
    bucket: _FakeBucket
    tasks: MagicMock


def _subject(bucket: _FakeBucket) -> _Subject:
    tasks = MagicMock()
    crawler = S3Crawler(
        s3_client=bucket,  # type: ignore[arg-type]
        bucket_name=BUCKET,
        bucket_alias="stick",
        file_storage_service=InMemoryFileStorageLazyBytesService(threshold_bytes=64),
        task_scheduling_service=tasks,
    )
    return _Subject(crawler=crawler, bucket=bucket, tasks=tasks)


def _bucket(objects: dict[str, bytes], spacing_minutes: int = 1) -> _FakeBucket:
    stamps = {
        name: NOW - timedelta(minutes=spacing_minutes * index)
        for index, name in enumerate(objects)
    }
    return _FakeBucket(objects=objects, stamps=stamps)


def test_one_poll_dispatches_a_plain_file_and_remembers_it():
    subject = _subject(_bucket({"report.pdf": b"%PDF-1.7 payload"}))

    outcome = subject.crawler.poll_once()

    assert outcome.dispatched == 1
    assert outcome.failed == 0
    assert subject.tasks.dispatch_index_file.call_count == 1
    assert subject.tasks.dispatch_index_archive.call_count == 0
    assert subject.crawler.processed.names == frozenset({"report.pdf"})

    # And the second poll finds nothing left to do.
    assert not subject.crawler.poll_once().found_anything


def test_one_poll_routes_a_loom_archive_to_the_archive_task():
    """The prescreen decides this from range reads; the loop has to act on it."""
    subject = _subject(_bucket({"backup.loom.zip": _loom_archive_bytes()}))

    outcome = subject.crawler.poll_once()

    assert outcome.dispatched == 1
    assert subject.tasks.dispatch_index_archive.call_count == 1
    assert subject.tasks.dispatch_index_file.call_count == 0


def test_a_poll_takes_at_most_its_batch_and_leaves_the_rest_for_the_next_one():
    """The bound that keeps the ledger moving during the drain of a whole stick."""
    subject = _subject(_bucket({f"{n}.pdf": b"payload" for n in range(5)}))

    first = subject.crawler.poll_once(limit=2)

    assert first.dispatched == 2
    assert first.deferred == 3

    second = subject.crawler.poll_once(limit=2)

    assert second.dispatched == 2
    assert second.deferred == 1
    assert len(subject.crawler.processed.names) == 4


def test_the_watermark_cannot_pass_an_object_the_poll_deferred():
    """Otherwise the tail of a large mirror is declared done without being read."""
    subject = _subject(_bucket({f"{n}.pdf": b"payload" for n in range(4)}))

    subject.crawler.poll_once(limit=1)

    watermark = subject.crawler.processed.watermark
    oldest = min(subject.bucket.stamps.values())
    assert watermark is not None and watermark < oldest


def test_an_object_that_could_not_be_handled_is_not_recorded_and_comes_back():
    """Nothing is recorded until it has actually been dispatched.

    The failure is injected at the dispatch rather than at the read, because a read
    failure goes round `retry`'s five ten-second attempts first -- same branch of the
    loop, forty seconds cheaper.
    """
    bucket = _bucket({"good.pdf": b"payload", "bad.pdf": b"payload"})
    subject = _subject(bucket)
    refused = {"bad.pdf"}

    def dispatch(full_name: str, **_: object) -> None:
        if any(name in full_name for name in refused):
            raise RuntimeError("dispatch refused")

    subject.tasks.dispatch_index_file.side_effect = dispatch

    outcome = subject.crawler.poll_once()

    assert outcome.failed == 1
    assert subject.crawler.processed.names == frozenset({"good.pdf"})

    refused.clear()
    again = subject.crawler.poll_once()

    assert again.dispatched == 1
    assert subject.crawler.processed.names == frozenset({"good.pdf", "bad.pdf"})
