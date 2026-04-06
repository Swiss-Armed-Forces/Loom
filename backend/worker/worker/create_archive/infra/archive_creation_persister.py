from common.archive.archive_repository import Archive, ArchiveRepository
from common.dependencies import get_archive_repository
from common.services.lazybytes_service import LazyBytes

from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _set_state(obj: Archive, state: str) -> None:
    obj.state = state


def _set_plain_file_storage_data(obj: Archive, storage_data: LazyBytes) -> None:
    obj.plain_file.storage_data = storage_data


def _set_encrypted_file_storage_data(obj: Archive, storage_data: LazyBytes) -> None:
    obj.encrypted_file.storage_data = storage_data


def _set_plain_file_checksum(obj: Archive, checksum: str) -> None:
    obj.plain_file.sha256 = checksum


def _set_encrypted_file_checksum(obj: Archive, checksum: str) -> None:
    obj.encrypted_file.sha256 = checksum


def _set_plain_file_size(obj: Archive, size: int) -> None:
    obj.plain_file.size = size


def _set_encrypted_file_size(obj: Archive, size: int) -> None:
    obj.encrypted_file.size = size


class ArchiveCreationPersister(PersisterBase[Archive]):
    @classmethod
    def get_repository(cls) -> ArchiveRepository:
        repository = get_archive_repository()
        return repository

    # Bind mutations as class attributes
    set_state = mutation(_set_state)
    set_plain_file_storage_data = mutation(_set_plain_file_storage_data)
    set_encrypted_file_storage_data = mutation(_set_encrypted_file_storage_data)
    set_plain_file_checksum = mutation(_set_plain_file_checksum)
    set_encrypted_file_checksum = mutation(_set_encrypted_file_checksum)
    set_plain_file_size = mutation(_set_plain_file_size)
    set_encrypted_file_size = mutation(_set_encrypted_file_size)
