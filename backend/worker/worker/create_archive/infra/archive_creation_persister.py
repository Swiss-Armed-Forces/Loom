from common.archive.archive_repository import Archive, ArchiveRepository
from common.dependencies import get_archive_repository
from common.services.lazybytes_service import LazyBytes

from worker.utils.persister_base import PersisterBase


class ArchiveCreationPersister(PersisterBase[Archive]):
    @classmethod
    def get_repository(cls) -> ArchiveRepository:
        repository = get_archive_repository()
        return repository

    def set_state(self, state: str):
        self._object.state = state

    def set_plain_file_storage_data(self, storage_data: LazyBytes):
        self._object.plain_file.storage_data = storage_data

    def set_encrypted_file_storage_data(self, storage_data: LazyBytes):
        self._object.encrypted_file.storage_data = storage_data

    def set_plain_file_checksum(self, checksum: str):
        self._object.plain_file.sha256 = checksum

    def set_encrypted_file_checksum(self, checksum: str):
        self._object.encrypted_file.sha256 = checksum

    def set_plain_file_size(self, size: int):
        self._object.plain_file.size = size

    def set_encrypted_file_size(self, size: int):
        self._object.encrypted_file.size = size
