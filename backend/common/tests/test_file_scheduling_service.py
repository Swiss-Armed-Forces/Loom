from unittest.mock import MagicMock
from uuid import uuid4

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


def test_reindex_file_preserves_recursion_depth(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
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
    old_file.flagged = False

    file_repository.get_by_id.return_value = old_file

    file_scheduling_service.reindex_file(uuid4())

    file_repository.save.assert_called_once()
    saved_file = file_repository.save.call_args.args[0]
    assert saved_file.recursion_depth == 2
