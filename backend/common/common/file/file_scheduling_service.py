"""Service to schedule new files for processing."""

import logging
from uuid import UUID

from bson import ObjectId

from common.file.file_repository import (
    File,
    FileNotFoundException,
    FilePurePath,
    FileRepository,
    Tag,
)
from common.services.file_storage_service import FileStorageService
from common.services.lazybytes_service import LazyBytes, LazyBytesService
from common.services.task_scheduling_service import (
    TaskSchedulingService,
    UpdateFileRequest,
)
from common.settings import settings
from common.utils.iterhash import CountingHash, iterhash

logger = logging.getLogger(__name__)


class FileSchedulingService:
    """Handles new files, stores them and schedules tasks."""

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        file_repository: FileRepository,
        file_storage_service: LazyBytesService,
        task_scheduling_service: TaskSchedulingService,
        lazybytes_service: LazyBytesService,
        file_storage_service_legacy: FileStorageService | None = None,
    ):
        self._file_repository = file_repository
        self._file_storage_service = file_storage_service
        self._task_scheduling_service = task_scheduling_service
        self._lazybytes_service = lazybytes_service
        self._file_storage_service_legacy = file_storage_service_legacy

    def index_file(
        self,
        full_name: str,
        file_content: LazyBytes,
        source_id: str,
        parent_id: UUID | None,
    ) -> File:
        logger.info("Scheduling indexing of file: '%s'", full_name)

        logger.info("Uploading '%s' to file storage", full_name)

        # Wrap data stream with hash and byte count tracking
        data_hash = CountingHash("sha256")
        data = iterhash(data_hash, self._lazybytes_service.load_generator(file_content))

        # Upload to file storage
        file_storage_handle = self._file_storage_service.from_generator(data)

        logger.info("Uploaded '%s' to file storage", full_name)

        file = File(
            storage_data=file_storage_handle,
            full_name=FilePurePath(full_name),
            source=source_id,
            parent_id=parent_id,
            sha256=data_hash.hexdigest(),
            size=data_hash.bytes_count,
        )

        # deduplicate file -> do not index the same file twice
        deduplicated_file = self._file_repository.get_by_deduplication_fingerprint(
            file.deduplication_fingerprint
        )
        if deduplicated_file is not None:
            # duplicate found:
            # - delete uploaded raw file
            # - return duplicate
            logger.info("Deduplication of file: '%s'", full_name)
            self._file_storage_service.delete(file_storage_handle)
            return deduplicated_file

        self._file_repository.save(file)

        if not settings.automatic_indexing:
            return file

        self._task_scheduling_service.index_file(file, file_content)

        return file

    def reindex_file(self, file_id: UUID):
        old_file = self._file_repository.get_by_id(file_id)
        if old_file is None:
            raise FileNotFoundException("Invalid file")

        # Handle legacy files: migrate from legacy file storage
        if old_file.storage_data is None:
            if old_file.storage_id is None:
                raise ValueError(
                    f"Cannot reindex file '{old_file.full_name}': "
                    "no storage data or storage_id"
                )

            logger.info(
                "Migrating file '%s' from legacy file storage",
                old_file.full_name,
            )

            # Load from legacy GridFS storage
            if self._file_storage_service_legacy is None:
                raise ValueError(
                    f"Cannot migrate file '{old_file.full_name}': "
                    "legacy file storage service not configured"
                )

            legacy_data_stream = (
                self._file_storage_service_legacy.open_download_iterator(
                    file_id=ObjectId(old_file.storage_id)
                )
            )

            # Upload to new file storage service
            storage_data = self._file_storage_service.from_generator(legacy_data_stream)
        else:
            storage_data = old_file.storage_data

        logger.info("Scheduling re-index of file '%s'", old_file.full_name)

        # Create a new minimal file object (same pattern as index_file)
        file = File(
            storage_data=storage_data,
            full_name=old_file.full_name,
            source=old_file.source,
            parent_id=old_file.parent_id,
            sha256=old_file.sha256,
            size=old_file.size,
            state="reindexing",
            reindex_count=old_file.reindex_count + 1,
            tags=old_file.tags,
        )
        # Preserve the original file ID
        file.es_meta.id = file_id

        # Save the minimal file
        self._file_repository.save(file)

        # Load file content and schedule indexing
        storage_data_stream = self._file_storage_service.load_generator(storage_data)
        lazybytes = self._lazybytes_service.from_generator(storage_data_stream)
        self._task_scheduling_service.index_file(file, lazybytes)

    def translate_file(self, file_id: UUID, lang: str):
        # update status
        file_to_translate = self._file_repository.get_by_id(file_id)
        if not file_to_translate:
            raise FileNotFoundException("No file to translate found")

        logger.info("Scheduling translation of file '%s'", file_to_translate.full_name)
        file_to_translate.state = "translating"
        self._file_repository.update(file_to_translate, include={"state"})

        self._task_scheduling_service.translate_files_by_id(file_id, lang)

    def summarize_file(self, file_id: UUID, system_prompt: str | None = None):
        # update status
        file_to_summarize = self._file_repository.get_by_id(file_id)
        if not file_to_summarize:
            raise FileNotFoundException("No file to summarize found")

        logger.info(
            "Scheduling summarization of file '%s'", file_to_summarize.full_name
        )
        file_to_summarize.state = "summarizing"
        self._file_repository.update(file_to_summarize, include={"state"})

        self._task_scheduling_service.summarize_files_by_id(file_id, system_prompt)

    def update_file(self, file_id: UUID, request: UpdateFileRequest):
        file = self._file_repository.get_by_id(file_id)
        if not file:
            raise FileNotFoundException("No file to hide found")
        file.state = "updating"
        self._file_repository.update(file, include={"state"})
        self._task_scheduling_service.update_by_id(file_id, request)

    def add_tags(self, file_id: UUID, tags: list[Tag]):
        # Add Tags to File
        file_to_add_tag = self._file_repository.get_by_id(file_id)
        if not file_to_add_tag:
            raise FileNotFoundException("No file to add tag found")
        file_to_add_tag.state = "tagging"
        self._file_repository.update(file_to_add_tag, include={"state"})
        self._task_scheduling_service.add_tag_to_file_by_id(file_id, tags)

    def remove_tag(self, file_id: UUID, tag: Tag):
        # Add Tags to File
        file_to_remove_tag = self._file_repository.get_by_id(file_id)
        if not file_to_remove_tag:
            raise FileNotFoundException("No file to remove tag found")
        file_to_remove_tag.state = "untagging"
        self._file_repository.update(file_to_remove_tag, include={"state"})
        self._task_scheduling_service.remove_tag_from_file_by_id(file_id, tag)
