from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from common.dependencies import (
    get_file_repository,
    get_task_scheduling_service,
)
from common.file.file_repository import File, FilePurePath
from common.file.file_scheduling_service import FileSchedulingService
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    InMemoryTempLazyBytesService,
)

LAZYBYTES_THRESHOLD_BYTES = 64
UPLOADED_AT = datetime(2026, 3, 1, 8, 30, tzinfo=timezone.utc)


def test_index_file(lazybytes_service_inmemory: InMemoryTempLazyBytesService):
    file_storage_service = InMemoryFileStorageLazyBytesService(
        threshold_bytes=LAZYBYTES_THRESHOLD_BYTES
    )
    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = None

    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        file_storage_service,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file_scheduling_service.index_file(
        full_name="test",
        file_content=file_storage_service.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
    )

    file_repository.save.assert_called_once()
    task_scheduling_service.index_file.assert_called_once()


def test_index_file_duplicate(lazybytes_service_inmemory: InMemoryTempLazyBytesService):
    file_storage_service = InMemoryFileStorageLazyBytesService(
        threshold_bytes=LAZYBYTES_THRESHOLD_BYTES
    )
    file_duplicate = MagicMock(spec=File)
    file_duplicate.attachments_skipped = False
    file_duplicate.recursion_depth = 0

    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = file_duplicate

    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        file_storage_service,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file = file_scheduling_service.index_file(
        full_name="test",
        file_content=file_storage_service.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
    )
    assert file == file_duplicate

    file_repository.save.assert_not_called()
    task_scheduling_service.index_file.assert_not_called()


def test_index_file_sets_recursion_depth(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = None

    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        lazybytes_service_inmemory,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file_scheduling_service.index_file(
        full_name="test",
        file_content=lazybytes_service_inmemory.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
        recursion_depth=3,
    )

    file_repository.save.assert_called_once()
    saved_file = file_repository.save.call_args.args[0]
    assert saved_file.recursion_depth == 3


@pytest.mark.parametrize(
    "additional_recursion_depth,expected_max_recursion_depth",
    [(0, 2), (3, 5)],
)
def test_reindex_file_offsets_the_depth_by_the_files_own(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    additional_recursion_depth: int,
    expected_max_recursion_depth: int,
):
    """`additional_recursion_depth` is relative to the file's own depth.

    The file keeps its place in the attachment hierarchy across a reindex, so the
    absolute ceiling handed to the indexing tasks is that depth plus the requested
    number of further levels.
    """
    file_repository = get_file_repository()
    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        lazybytes_service_inmemory,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    old_file = MagicMock(spec=File)
    old_file.storage_data = lazybytes_service_inmemory.from_bytes(b"content")
    old_file.recursion_depth = 2
    old_file.full_name = FilePurePath("test.txt")
    old_file.source = "test-source"
    old_file.parent_id = None
    old_file.sha256 = "abc123"
    old_file.size = 7
    old_file.reindex_count = 0
    old_file.tags = []
    old_file.archives = []
    old_file.flagged = False
    old_file.uploaded_datetime = UPLOADED_AT

    file_repository.get_by_id.return_value = old_file

    file_scheduling_service.reindex_file(uuid4(), additional_recursion_depth)

    file_repository.save.assert_called_once()
    saved_file = file_repository.save.call_args.args[0]
    assert saved_file.recursion_depth == 2

    task_scheduling_service.index_file.assert_called_once()
    assert (
        task_scheduling_service.index_file.call_args.kwargs["max_recursion_depth"]
        == expected_max_recursion_depth
    )


@pytest.mark.parametrize(
    "attachments_skipped,max_recursion_depth,expected_reindex",
    [
        # The duplicate's own subtree was cut short and this request reaches past it.
        (True, 3, True),
        # Nothing was cut short, so there is nothing below it left to build.
        (False, 3, False),
        # Cut short, but this request reaches no further than the duplicate already is.
        (True, 1, False),
    ],
)
def test_index_file_deepens_a_deduplicated_file(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    attachments_skipped: bool,
    max_recursion_depth: int,
    expected_reindex: bool,
):
    """A duplicate is the only place a deeper second pass can be picked up.

    An attachment's deduplication fingerprint is deterministic, so re-indexing a
    container at a greater depth finds every already-extracted child here instead of
    dispatching it -- and the levels below it would never be built.
    """
    file_duplicate = MagicMock(spec=File)
    file_duplicate.id_ = uuid4()
    file_duplicate.storage_data = lazybytes_service_inmemory.from_bytes(b"test")
    file_duplicate.attachments_skipped = attachments_skipped
    file_duplicate.recursion_depth = 1
    file_duplicate.full_name = FilePurePath("test")
    file_duplicate.source = "SOURCE"
    file_duplicate.parent_id = None
    file_duplicate.sha256 = "abc123"
    file_duplicate.size = 4
    file_duplicate.reindex_count = 0
    file_duplicate.tags = []
    file_duplicate.archives = []
    file_duplicate.flagged = False
    file_duplicate.uploaded_datetime = UPLOADED_AT

    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = file_duplicate
    file_repository.get_by_id.return_value = file_duplicate

    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        lazybytes_service_inmemory,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file_scheduling_service.index_file(
        full_name="test",
        file_content=lazybytes_service_inmemory.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
        max_recursion_depth=max_recursion_depth,
    )

    if not expected_reindex:
        task_scheduling_service.index_file.assert_not_called()
        return

    # The duplicate sits at depth 1, so the reindex it triggers must reach exactly as
    # far as this request asked for -- no further, and no shorter.
    task_scheduling_service.index_file.assert_called_once()
    assert (
        task_scheduling_service.index_file.call_args.kwargs["max_recursion_depth"]
        == max_recursion_depth
    )


def test_reindex_file_keeps_the_original_upload_time(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    """A reindex is not a re-upload.

    `File.uploaded_datetime` defaults to now and this document is saved over the
    original id, so defaulting it would restamp the file -- and `reindex_lost_files.py`
    drives reindexing unattended while sorting on that very field, so every reindexed
    file would jump to the front of every date-ordered view.
    """
    file_repository = get_file_repository()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        lazybytes_service_inmemory,
        get_task_scheduling_service(),
        lazybytes_service_inmemory,
    )

    old_file = MagicMock(spec=File)
    old_file.storage_data = lazybytes_service_inmemory.from_bytes(b"content")
    old_file.recursion_depth = 2
    old_file.full_name = FilePurePath("test.txt")
    old_file.source = "test-source"
    old_file.parent_id = None
    old_file.sha256 = "abc123"
    old_file.size = 7
    old_file.reindex_count = 0
    old_file.tags = []
    old_file.archives = []
    old_file.flagged = False
    old_file.uploaded_datetime = UPLOADED_AT

    file_repository.get_by_id.return_value = old_file

    file_scheduling_service.reindex_file(uuid4(), 0)

    saved_file = file_repository.save.call_args.args[0]
    assert saved_file.uploaded_datetime == UPLOADED_AT


def test_a_file_defaults_its_upload_time_to_an_aware_one():
    """Every explicit writer of this field passes an aware value; so must the default.

    The field is indexed as an Elasticsearch Date and ordered on, and a naive value
    compares inconsistently with an aware one in Python long before Elasticsearch sees
    either.
    """
    file = File(
        storage_data=None,
        full_name=FilePurePath("test.txt"),
        source="test-source",
        sha256="abc123",
        size=7,
    )

    assert file.uploaded_datetime.tzinfo is not None
