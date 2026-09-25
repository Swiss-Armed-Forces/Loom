"""What the poll loop remembers, and what it is allowed to forget.

This bucket is now where a whole USB stick is mirrored, so "one entry per object ever
seen, for the life of the pod" stopped being a reasonable amount of state. The watermark
is what bounds it; these pin that it bounds it without ever skipping an object that has
not been handled.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from minio import Minio
from minio.datatypes import Object

from crawler.s3_crawler import WATERMARK_GRACE, S3Crawler

BUCKET = "loom-intake"
NOW = datetime(2026, 6, 7, 9, 0, 0, tzinfo=timezone.utc)


def _crawler() -> S3Crawler:
    return S3Crawler(
        s3_client=MagicMock(spec=Minio),
        bucket_name=BUCKET,
        bucket_alias=None,
        file_storage_service=MagicMock(),
        task_scheduling_service=MagicMock(),
    )


def _listed(name: str, at: datetime | None, size: int = 10) -> Object:
    return Object(BUCKET, name, last_modified=at, size=size)


def _process(crawler: S3Crawler, listing: list[Object]) -> None:
    """One successful pass over a listing, as the poll loop performs it."""
    for obj in crawler.unprocessed(listing):
        crawler.processed.record(obj)


def test_an_unseen_object_is_work_to_do():
    crawler = _crawler()

    fresh = crawler.unprocessed([_listed("a.pdf", NOW)])

    assert [obj.object_name for obj in fresh] == ["a.pdf"]
    assert fresh[0].size == 10


def test_an_object_already_processed_is_not_offered_again():
    crawler = _crawler()

    _process(crawler, [_listed("a.pdf", NOW)])

    assert not crawler.unprocessed([_listed("a.pdf", NOW)])


def test_the_watermark_only_moves_once_something_has_been_processed():
    """An empty crawler must never skip anything -- including on a fresh pod."""
    crawler = _crawler()

    crawler.processed.advance()

    assert crawler.processed.watermark is None
    assert crawler.unprocessed([_listed("old.pdf", NOW - timedelta(days=30))])


def test_everything_below_the_watermark_is_forgotten():
    """The bound on memory: the set must not keep growing with the bucket."""
    crawler = _crawler()
    old = NOW - WATERMARK_GRACE * 3
    _process(
        crawler,
        [_listed(f"old-{n}.pdf", old) for n in range(100)] + [_listed("new.pdf", NOW)],
    )

    crawler.processed.advance()

    assert crawler.processed.watermark == NOW - WATERMARK_GRACE
    assert crawler.processed.names == frozenset({"new.pdf"})


def test_an_object_below_the_watermark_is_not_crawled_again():
    """Forgetting it has to mean "done", not "new" -- or it is re-indexed forever."""
    crawler = _crawler()
    _process(crawler, [_listed("old.pdf", NOW - WATERMARK_GRACE * 2)])
    _process(crawler, [_listed("new.pdf", NOW)])
    crawler.processed.advance()

    assert not crawler.unprocessed([_listed("old.pdf", NOW - WATERMARK_GRACE * 2)])


def test_an_object_written_during_a_poll_is_still_ahead_of_the_watermark():
    """The grace period is the safety margin, and this is what it buys.

    The watermark trails the newest processed object by an hour, so an object that
    became visible late -- clock skew, an out-of-order listing -- is still picked up.
    """
    crawler = _crawler()
    _process(crawler, [_listed("new.pdf", NOW)])
    crawler.processed.advance()

    late = _listed("late.pdf", NOW - timedelta(minutes=5))

    assert [obj.object_name for obj in crawler.unprocessed([late])] == ["late.pdf"]


def test_an_object_with_no_timestamp_is_skipped_rather_than_crashing():
    crawler = _crawler()

    assert not crawler.unprocessed([_listed("a.pdf", None)])
    assert not crawler.unprocessed([_listed("", NOW)])
