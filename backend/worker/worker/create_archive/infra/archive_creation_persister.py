from bson import ObjectId
from common.archive.archive_repository import Archive, ArchiveRepository
from common.dependencies import get_archive_repository

from worker.utils.persister_base import PersisterBase


class ArchiveCreationPersister(PersisterBase[Archive]):
    @classmethod
    def get_repository(cls) -> ArchiveRepository:
        repository = get_archive_repository()
        return repository

    def set_state(self, state: str):
        self._object.state = state

    def set_plain_file_storage_id(self, storage_id: ObjectId):
        self._object.plain_file.storage_id = str(storage_id)

    def set_encrypted_file_storage_id(self, storage_id: ObjectId):
        self._object.encrypted_file.storage_id = str(storage_id)

    def set_plain_file_checksum(self, checksum: str):
        self._object.plain_file.sha256 = checksum

    def set_encrypted_file_checksum(self, checksum: str):
        self._object.encrypted_file.sha256 = checksum

    def set_plain_file_size(self, size: int):
        self._object.plain_file.size = size

    def set_encrypted_file_size(self, size: int):
        self._object.encrypted_file.size = size
