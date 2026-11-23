import heapq
import logging
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import sleep

from common.llm.exceptions import LLMPermanentError, classify_llm_error
from common.llm.return_types import IndexingUrgency
from common.services.lazybytes_service import FileStorageTag, LazyBytesService
from common.services.task_scheduling_service import (
    ArchiveImportRequest,
    IndexingPriority,
    TaskSchedulingService,
)
from common.utils.file_size import file_size_to_string
from common.utils.retry import retry
from minio import Minio
from minio.datatypes import Object
from pydantic_ai import Agent

from crawler.archive_prescreen import IntakeObjectKind, classify_intake_object
from crawler.settings import settings

logger = logging.getLogger(__name__)

S3_OBJECT_POLL_INTERVAL_S: int = 5
S3_READ_CHUNK_SIZE: int = 1 * 1024 * 1024
S3_RETRY_MAX_ATTEMPTS: int = 5
S3_RETRY_WAIT_S: int = 10
S3_MAX_CONCURRENT_DOWNLOADS: int = 4

# The ceiling the poll interval backs off to while nothing new is arriving.
#
# Listing is not free: S3 has no "objects newer than X", so every poll pages the whole
# bucket, and nothing ever deletes from `loom-intake` (see `WATERMARK_GRACE`), so the
# listing grows monotonically with every stick ever ingested. At five seconds flat, a
# 300k-object bucket is roughly 60 requests a second against the gateway forever, to
# discover nothing. Backing off only costs latency on the poll that finds the first
# object of a new stick; the interval drops straight back to the floor from there.
S3_OBJECT_POLL_MAX_INTERVAL_S: int = 60

# How many new objects one poll hands to the download pool.
#
# The first poll after a stick lands sees the whole stick. Submitting all of it queues
# hundreds of thousands of callables into the executor's unbounded work queue, and the
# rest of this loop -- the ledger, the watermark -- does not move again until the last
# of them is done. A bounded batch keeps the ledger advancing and bounds what a pod
# restart re-downloads; the remainder is simply picked up by the next poll, and
# `advance` is told about it so the watermark cannot run past it.
S3_MAX_OBJECTS_PER_POLL: int = 1000

# How far behind the newest object it has taken the crawler still remembers
# individual objects for.
#
# Without a watermark the record of what has been processed grows for the life of the
# pod, one entry per object ever seen. This bucket is where a whole USB stick is
# mirrored (nixos/usb-ingest.nix defaults `--bucket loom-intake`, and nothing deletes
# from it afterwards), so three sticks in, that set is hundreds of thousands of entries
# that are never released.
#
# Anything older than this is taken as already done. That is safe because S3 stamps
# `last_modified` when the object is *written*: nothing puts an old timestamp on a
# new object, since `mc mirror` is run without `--preserve`. The window is therefore
# only covering clock skew between the gateway and this pod, and objects that became
# visible out of order -- both of which are seconds, not an hour.
WATERMARK_GRACE = timedelta(hours=1)


# `slots=True` on both of the per-object records below, because there are hundreds of
# thousands of them: a slotted instance costs about half what a `__dict__`-carrying one
# does, and at 300k objects that is tens of megabytes against the crawler's
# `memory: "1.5Gi"`.
@dataclass(frozen=True, slots=True)
class _ProcessedObject:
    object_name: str
    last_modified: datetime


class ProcessedLedger:
    """What has already been handled, and the watermark that bounds how much is kept.

    One object rather than a set and a datetime side by side on the crawler, because
    they are one rule: an object is done if it is remembered individually *or* if it
    is old enough that the watermark speaks for it, and the two only stay consistent
    if they move together.
    """

    def __init__(self) -> None:
        self._seen: set[_ProcessedObject] = set()
        # The newest timestamp ever recorded, maintained here rather than scanned for
        # in `advance`: the scan is O(|seen|) and `advance` runs on every poll, so on a
        # long drain the loop pays roughly 75ms per poll at 300k entries to compute a
        # watermark it then discards at the no-op check below.
        self._newest: datetime | None = None
        # None until something has actually been processed, so a freshly started pod
        # never skips an object on the strength of a watermark it has not earned.
        self.watermark: datetime | None = None

    def __len__(self) -> int:
        return len(self._seen)

    @property
    def names(self) -> frozenset[str]:
        """The objects still remembered individually.

        For assertions. The size -- the quantity the watermark exists to bound -- is
        what `advance` logs.
        """
        return frozenset(entry.object_name for entry in self._seen)

    def covers(self, object_name: str, last_modified: datetime) -> bool:
        """Whether this object has been handled already."""
        if self.watermark is not None and last_modified <= self.watermark:
            return True
        return _ProcessedObject(object_name, last_modified) in self._seen

    def record(self, obj: "IntakeObject") -> None:
        """Remember an object, until the watermark comes to cover it."""
        self._seen.add(_ProcessedObject(obj.object_name, obj.last_modified))
        if self._newest is None or obj.last_modified > self._newest:
            self._newest = obj.last_modified

    def advance(self, oldest_unfinished: datetime | None = None) -> None:
        """Move the watermark up and forget everything it now covers.

        The grace period is what makes this safe rather than merely cheap: the
        watermark trails the newest processed object, so an object written while a
        poll was in flight is still ahead of it. See `WATERMARK_GRACE`.

        `oldest_unfinished` is the oldest object this poll did *not* finish -- a failed
        download, or one deferred to the next batch -- and the watermark never passes
        it. `covers` answers True for everything at or below the watermark whether or
        not it was ever recorded, so without this bound a single object that exhausted
        its retries early on a long mirror is declared done the moment a newer one
        succeeds, and nothing ever offers it again or says so.
        """
        if self._newest is None:
            return

        # Clamped to this pod's own clock, because the watermark can only ever move
        # forwards and a single object stamped in the future would therefore cover
        # every object written between now and that date -- silently, with
        # `unprocessed` answering an empty list and the loop backing off as if the
        # bucket were quiet. That is not exotic on an air-gapped box: a dead RTC with
        # no NTP, or a VM restored from a snapshot, writes to MinIO before the clock is
        # corrected, and nothing deletes from `loom-intake`, so a restart meets the
        # same object and is poisoned again.
        now = datetime.now(timezone.utc)
        newest = min(self._newest, now)
        if newest != self._newest:
            logger.warning(
                "Ignoring an object timestamp in the future (%s) for the watermark; "
                "using this pod's clock (%s) instead",
                self._newest,
                now,
            )

        watermark = newest - WATERMARK_GRACE
        if oldest_unfinished is not None:
            watermark = min(watermark, oldest_unfinished - WATERMARK_GRACE)
        if self.watermark is not None and watermark <= self.watermark:
            return

        self.watermark = watermark
        self._seen = {entry for entry in self._seen if entry.last_modified > watermark}
        logger.info(
            "Watermark advanced to %s; %d objects still remembered individually",
            watermark,
            len(self._seen),
        )


@dataclass(frozen=True, slots=True)
class IntakeObject:
    """One listed object, with the three fields this loop actually uses.

    A declared shape rather than minio's `Object` so the filtering below can be reasoned
    about -- and tested -- without a client.
    """

    object_name: str
    last_modified: datetime
    size: int


@dataclass(frozen=True, slots=True)
class FreshObjects:
    """What one poll found: the batch to take now, and what it leaves behind.

    `oldest_deferred` rather than the deferred objects themselves, because that is the
    only thing the loop asks of them -- the bound `advance` must not pass. Keeping the
    tail would mean holding the whole backlog of a large mirror in memory for the sake
    of one timestamp.
    """

    batch: list[IntakeObject]
    total: int
    oldest_deferred: datetime | None

    @property
    def deferred(self) -> int:
        return self.total - len(self.batch)


@dataclass(frozen=True, slots=True)
class PollOutcome:
    """What one pass of the poll loop did."""

    dispatched: int
    failed: int
    deferred: int

    @property
    def found_anything(self) -> bool:
        return bool(self.dispatched or self.failed or self.deferred)


# The rubric the decision model scores against, as the broker's own priorities. The
# two are separate types because they answer to different things: the levels have to be
# contiguous from zero and described for a decision model to read them as a rubric,
# while `TaskPriority`'s values are the RabbitMQ bands.
_URGENCY_TO_PRIORITY: dict[IndexingUrgency, IndexingPriority] = {
    IndexingUrgency.LOW: IndexingPriority.LOW,
    IndexingUrgency.MEDIUM: IndexingPriority.MEDIUM,
    IndexingUrgency.HIGH: IndexingPriority.HIGH,
}


class S3Crawler:
    # Each poll keeps its own ledger, executor, watermark state and decision agent.
    # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        s3_client: Minio,
        bucket_name: str,
        bucket_alias: str | None,
        file_storage_service: LazyBytesService[FileStorageTag],
        task_scheduling_service: TaskSchedulingService,
        index_prioritization_agent: Agent[None, IndexingUrgency],
    ):
        self.client = s3_client
        self.bucket_name = bucket_name
        self.display_name = bucket_alias if bucket_alias else bucket_name
        self.file_storage_service = file_storage_service
        self.task_scheduling_service = task_scheduling_service
        self.processed = ProcessedLedger()
        self._executor = ThreadPoolExecutor(max_workers=S3_MAX_CONCURRENT_DOWNLOADS)
        self.index_prioritization_agent = index_prioritization_agent
        self._index_prioritization_unavailable = False

    def _full_name(self, object_name: str) -> str:
        return str(Path(f"//{self.display_name}/{object_name}"))

    def _deduce_priority(self, full_name: str, size: int) -> IndexingPriority:
        """Ask the decision model how soon this object should be indexed.

        Every object the crawler takes is ranked, and the answer rides on the
        `ArchiveImportRequest` as well as on `dispatch_index_file`, so a blob that turns
        out not to be an importable archive keeps it. A priority hint is advisory, so
        nothing here may fail a download: an unanswerable question falls back to
        `MEDIUM`, which is `dispatch_index_file`'s own default. Note `TaskPriority` puts
        LOW and MEDIUM in one RabbitMQ quorum band, so of the three answers only HIGH
        changes anything at the broker.

        A permanent failure -- a model name the service answers 404 for, a model that is
        not a decision model -- reproduces on every object, and a mirrored stick is
        hundreds of thousands of them. It is reported once and then stops being asked,
        rather than buying the same warning and the same round trip per object.
        """
        if self._index_prioritization_unavailable:
            return IndexingPriority.MEDIUM

        try:
            result = self.index_prioritization_agent.run_sync(
                f"Path/filename: {full_name}. Size: {file_size_to_string(size)}"
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            classified = classify_llm_error(ex, "Priority inference failed")
            if isinstance(classified, LLMPermanentError):
                self._index_prioritization_unavailable = True
                logger.warning(
                    "Priority inference is unusable; every object of this poll loop "
                    "is indexed at the default priority from here on",
                    exc_info=classified,
                )
            else:
                logger.warning(
                    "Priority inference failed for %s; using the default",
                    full_name,
                    exc_info=classified,
                )
            return IndexingPriority.MEDIUM

        return _URGENCY_TO_PRIORITY[result.output]

    def _download_object(
        self, object_name: str, size: int, priority: IndexingPriority
    ) -> None:
        logger.info("Downloading object %s", object_name)
        full_name = self._full_name(object_name)
        source = f"{settings.crawler_source_id}/{self.bucket_name}"

        # Classified before the body is fetched. The crawler is the only part of
        # Loom holding an S3 client pointed at the object, which is what makes
        # an exact answer cost a few range reads here and a full extra
        # download-to-disk anywhere else -- see archive_prescreen.
        kind = classify_intake_object(self.client, self.bucket_name, object_name, size)

        def stream_generator():
            response = self.client.get_object(self.bucket_name, object_name)
            try:
                yield from response.stream(S3_READ_CHUNK_SIZE)
            finally:
                # minio requires both calls, otherwise the buffered response and its
                # connection stay alive - notably when retry() abandons a partially
                # consumed stream.
                response.close()
                response.release_conn()

        # Aware: this is indexed as an Elasticsearch Date and ordered on, and a naive
        # local timestamp sorts inconsistently against anything written with a zone.
        uploaded_at = datetime.now(timezone.utc)
        file_content = retry(
            lambda: self.file_storage_service.from_generator(stream_generator())
        )

        if kind is IntakeObjectKind.PLAIN_FILE:
            self.task_scheduling_service.dispatch_index_file(
                full_name=full_name,
                file_content=file_content,
                source_id=source,
                parent_id=None,
                uploaded_datetime=uploaded_at,
                priority=priority,
            )
            return

        logger.info("Object %s is a %s; importing it as an archive", object_name, kind)
        self.task_scheduling_service.dispatch_index_archive(
            ArchiveImportRequest(
                file_content=file_content,
                full_name=full_name,
                source_id=source,
                uploaded_datetime=uploaded_at,
                priority=priority,
                # Nobody asked for this one: it was found in the intake bucket, which
                # on an appliance means it came off a stick. The router declines to
                # unpack an archive that would not fit on the disk three times over.
                unattended=True,
            )
        )

    def crawl(self) -> None:
        logger.info(
            "Starting crawler for bucket '%s' (display name: '%s'), "
            "poll interval: %ds-%ds",
            self.bucket_name,
            self.display_name,
            S3_OBJECT_POLL_INTERVAL_S,
            S3_OBJECT_POLL_MAX_INTERVAL_S,
        )
        logger.info("Entering poll loop")
        interval = S3_OBJECT_POLL_INTERVAL_S
        while True:
            outcome = self.poll_once()

            # Backed off only while the bucket is quiet, and reset by the first new
            # object, so the latency that matters -- a stick that has just been
            # mirrored -- is still the floor.
            interval = (
                S3_OBJECT_POLL_INTERVAL_S
                if outcome.found_anything
                else min(interval * 2, S3_OBJECT_POLL_MAX_INTERVAL_S)
            )
            sleep(interval)

    def poll_once(self, limit: int = S3_MAX_OBJECTS_PER_POLL) -> PollOutcome:
        """One pass of the poll loop: list, download a batch, move the watermark.

        Split out of `crawl` so that a test can drive a single pass; `limit` is a
        parameter for the same reason.
        """
        logger.debug("Polling bucket '%s' for objects", self.bucket_name)

        # Filtered as the listing arrives, not after it has been collected. The
        # listing is the whole bucket -- S3 has no way to ask for "objects newer
        # than X", since `start_after` is lexicographic by key and these keys are
        # not in time order -- so after a few sticks it is hundreds of thousands of
        # entries. Sorting all of them every five seconds would be most of what this
        # loop does; materialising all of them first is hundreds of megabytes of minio
        # `Object`s allocated and discarded on every poll, in a pod that also holds
        # download buffers. `unprocessed` takes an iterable and touches no state the
        # retry would have to undo, so it is safe inside `retry`. What is new is a
        # handful.
        fresh = retry(
            lambda: self.unprocessed(
                self.client.list_objects(self.bucket_name, recursive=True),
                limit=limit,
            )
        )
        if fresh.deferred:
            logger.info(
                "Taking %d of %d new objects this poll; %d follow next poll",
                len(fresh.batch),
                fresh.total,
                fresh.deferred,
            )

        # The decision model is asked here rather than on a download thread. One
        # `Agent` is built per process and `run_sync` creates an event loop per thread
        # it is called from, so driving it from the four download threads would have
        # four loops sharing the provider's one `AsyncClient` -- and a keep-alive
        # connection reused across loops hangs rather than fails, holding a download
        # slot open for good.
        future_to_object = {}
        for obj in fresh.batch:
            logger.info("New object detected via polling: %s", obj.object_name)
            priority = self._deduce_priority(self._full_name(obj.object_name), obj.size)
            future_to_object[
                self._executor.submit(
                    self._download_object, obj.object_name, obj.size, priority
                )
            ] = obj

        # `as_completed` rather than iterating the mapping: the ledger is in-process
        # memory, so an object is only safe from being re-downloaded once it has
        # been recorded. Taking the futures in submission order means nothing is
        # recorded until the slowest of the batch is done -- hours, for a stick --
        # and a pod restart in the middle repeats every object already ingested.
        unfinished = [fresh.oldest_deferred] if fresh.oldest_deferred else []
        failed = 0
        for future in as_completed(future_to_object):
            processed_object = future_to_object[future]
            if exc := future.exception():
                logger.error(
                    "Failed to download object '%s': %s",
                    processed_object.object_name,
                    exc,
                )
                failed += 1
                unfinished.append(processed_object.last_modified)
            else:
                self.processed.record(processed_object)

        self.processed.advance(min(unfinished) if unfinished else None)
        return PollOutcome(
            dispatched=len(fresh.batch) - failed,
            failed=failed,
            deferred=fresh.deferred,
        )

    def unprocessed(
        self, listing: Iterable[Object], limit: int | None = None
    ) -> FreshObjects:
        """The objects in a listing that still have to be handled.

        Oldest first, and bounded: `limit` takes the oldest `limit` of them and reports
        only the *age* of what is left over. Both halves are about the drain of a large
        mirror. Newest-first would leave the oldest objects deferred, which pins
        `advance` to the age of the very first object on the stick for the whole drain
        -- so the ledger grows to the entire backlog and `WATERMARK_GRACE` bounds
        nothing in the one case that matters. And materialising the tail to
        take a minimum off it costs tens of megabytes per poll at a few hundred
        thousand objects, in a pod limited to 1.5 GiB; `heapq.nsmallest` holds `limit`
        of them instead.
        """
        total = 0

        def candidates() -> Iterator[IntakeObject]:
            nonlocal total
            for obj in listing:
                name = obj.object_name
                last_modified = obj.last_modified
                if not name or not last_modified:
                    continue
                if self.processed.covers(name, last_modified):
                    continue
                total += 1
                yield IntakeObject(
                    object_name=name,
                    last_modified=last_modified,
                    size=obj.size or 0,
                )

        if limit is None:
            batch = sorted(candidates(), key=lambda o: o.last_modified)
            return FreshObjects(batch=batch, total=total, oldest_deferred=None)

        # One more than asked for: the extra entry is the oldest deferred object, which
        # is the bound `advance` needs and the only thing the tail is read for.
        head = heapq.nsmallest(limit + 1, candidates(), key=lambda o: o.last_modified)
        if len(head) <= limit:
            return FreshObjects(batch=head, total=total, oldest_deferred=None)
        return FreshObjects(
            batch=head[:limit],
            total=total,
            oldest_deferred=head[limit].last_modified,
        )
