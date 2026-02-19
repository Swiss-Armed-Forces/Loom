from unittest.mock import MagicMock

from common.dependencies import (
    get_file_repository,
    get_file_storage_service,
    get_task_scheduling_service,
)
from common.file.file_repository import File
from common.file.file_scheduling_service import FileSchedulingService
from common.services.lazybytes_service import LazyBytesService


def test_index_file(lazybytes_service_inmemory: LazyBytesService):
    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = None

    file_storage_service = get_file_storage_service()
    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        file_storage_service,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file_scheduling_service.index_file(
        full_name="test",
        file_content=lazybytes_service_inmemory.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
    )

    file_repository.save.assert_called_once()
    task_scheduling_service.index_file.assert_called_once()


def test_index_file_duplicate(lazybytes_service_inmemory: LazyBytesService):
    file_duplicate = MagicMock(spec=File)

    file_repository = get_file_repository()
    file_repository.get_by_deduplication_fingerprint.return_value = file_duplicate

    file_storage_service = get_file_storage_service()
    task_scheduling_service = get_task_scheduling_service()
    file_scheduling_service = FileSchedulingService(
        file_repository,
        file_storage_service,
        task_scheduling_service,
        lazybytes_service_inmemory,
    )

    file = file_scheduling_service.index_file(
        full_name="test",
        file_content=lazybytes_service_inmemory.from_bytes(b"test"),
        source_id="SOURCE",
        parent_id=None,
    )
    assert file == file_duplicate

    file_repository.save.assert_not_called()
    task_scheduling_service.index_file.assert_not_called()
