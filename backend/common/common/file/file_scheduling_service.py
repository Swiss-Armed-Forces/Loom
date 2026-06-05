"""Service to schedule new files for processing."""

import logging
from datetime import datetime
from uuid import UUID

from common.file.file_repository import (
    File,
    FileNotFoundException,
    FilePurePath,
    FileRepository,
    FileWithoutStorageDataException,
    Tag,
)
from common.services.lazybytes_service import (
    FileStorageLazyBytes,
    FileStorageTag,
    LazyBytesService,
    TempStorageTag,
)
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
        file_storage_service: LazyBytesService[FileStorageTag],
        task_scheduling_service: TaskSchedulingService,
        lazybytes_service: LazyBytesService[TempStorageTag],
    ):
        self._file_repository = file_repository
        self._file_storage_service = file_storage_service
        self._task_scheduling_service = task_scheduling_service
        self._lazybytes_service = lazybytes_service

    def index_file(
        self,
        full_name: str,
        file_content: FileStorageLazyBytes,
        source_id: str,
        parent_id: UUID | None,
        uploaded_datetime: datetime | None = None,
        recursion_depth: int = 0,
    ) -> File:
        """Schedule indexing of a file.

        Args:
            full_name: The full path/name of the file.
            file_content: LazyBytes handle pointing to file_storage_service (permanent).
            source_id: Source identifier for the file.
            parent_id: Optional parent file ID for nested files.
            uploaded_datetime: Timestamp to use as the file's upload time. Should be
                captured at dispatch time to preserve ordering when tasks run in
                parallel. Defaults to now() if not provided.
            recursion_depth: Nesting depth of this file within the attachment hierarchy.
                0 for root files, incremented by 1 for each level of attachment
                extraction. Used to enforce settings.max_recursion_depth limits.

        Returns:
            The created File object.

        Note:
            file_content is expected to already be in file_storage_service.
            This method copies it to lazybytes_service for processing (disposable copy),
            while keeping file_content as the permanent storage_data reference.
        """
        logger.info("Scheduling indexing of file: '%s'", full_name)

        # file_content is already in file_storage_service (permanent storage)
        # Load from file_storage_service and copy to lazybytes_service (for processing)
        logger.info("Creating lazybytes copy for processing: '%s'", full_name)

        # Wrap data stream with hash and byte count tracking
        data_hash = CountingHash("sha256")
        data = iterhash(
            data_hash, self._file_storage_service.load_generator(file_content)
        )

        # Copy to lazybytes for processing (disposable copy)
        lazybytes_handle = self._lazybytes_service.from_generator(data)

        file = File(
            storage_data=file_content,
            full_name=FilePurePath(full_name),
            source=source_id,
            parent_id=parent_id,
            sha256=data_hash.hexdigest(),
            size=data_hash.bytes_count,
            uploaded_datetime=uploaded_datetime or datetime.now(),
            recursion_depth=recursion_depth,
        )

        # deduplicate file -> do not index the same file twice
        deduplicated_file = self._file_repository.get_by_deduplication_fingerprint(
            file.deduplication_fingerprint
        )
        if deduplicated_file is not None:
            # duplicate found:
            # - delete uploaded raw file from permanent storage
            # - delete lazybytes copy
            # - return duplicate
            logger.info("Deduplication of file: '%s'", full_name)
            self._file_storage_service.delete(file_content)
            self._lazybytes_service.delete(lazybytes_handle)
            return deduplicated_file

        self._file_repository.save(file)

        if not settings.automatic_indexing:
            # Clean up lazybytes copy since we won't be indexing
            self._lazybytes_service.delete(lazybytes_handle)
            return file

        self._task_scheduling_service.index_file(file, lazybytes_handle)

        return file

    def reindex_file(self, file_id: UUID):
        old_file = self._file_repository.get_by_id(file_id)
        if old_file is None:
            raise FileNotFoundException(f"Could not find file with id: {file_id}")

        # Create a new minimal file object (same pattern as index_file)
        storage_data = old_file.storage_data
        if storage_data is None:
            raise FileWithoutStorageDataException(
                f"Can not reindex file (id: {file_id}) with no storage data"
            )

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
            flagged=old_file.flagged,
            recursion_depth=0,
        )
        # Preserve the original file ID
        file.es_meta.id = file_id

        # Save the minimal file
        self._file_repository.save(file)

        # Load file content and schedule indexing
        storage_data_stream = self._file_storage_service.load_generator(storage_data)
        lazybytes = self._lazybytes_service.from_generator(storage_data_stream)

        logger.info("Scheduling re-index of file '%s'", old_file.full_name)
        self._task_scheduling_service.index_file(file, lazybytes)

    def translate_file(self, file_id: UUID, lang: str):
        # update status
        file_to_translate = self._file_repository.get_by_id(file_id)
        if not file_to_translate:
            raise FileNotFoundException("No file to translate found")

        logger.info("Scheduling translation of file '%s'", file_to_translate.full_name)
        self._task_scheduling_service.translate_files_by_id(file_id, lang)

    def summarize_file(self, file_id: UUID, system_prompt: str | None = None):
        # update status
        file_to_summarize = self._file_repository.get_by_id(file_id)
        if not file_to_summarize:
            raise FileNotFoundException("No file to summarize found")

        logger.info(
            "Scheduling summarization of file '%s'", file_to_summarize.full_name
        )
        self._task_scheduling_service.summarize_files_by_id(file_id, system_prompt)

    def describe_image(self, file_id: UUID, system_prompt: str | None = None):
        file_to_describe = self._file_repository.get_by_id(file_id)
        if not file_to_describe:
            raise FileNotFoundException("No file to describe found")

        logger.info(
            "Scheduling image description of file '%s'", file_to_describe.full_name
        )
        self._task_scheduling_service.describe_image_by_id(file_id, system_prompt)

    def update_file(self, file_id: UUID, request: UpdateFileRequest):
        file = self._file_repository.get_by_id(file_id)
        if not file:
            raise FileNotFoundException("No file to hide found")
        self._task_scheduling_service.update_by_id(file_id, request)

    def add_tags(self, file_id: UUID, tags: list[Tag]):
        # Add Tags to File
        file_to_add_tag = self._file_repository.get_by_id(file_id)
        if not file_to_add_tag:
            raise FileNotFoundException("No file to add tag found")
        self._task_scheduling_service.add_tag_to_file_by_id(file_id, tags)

    def remove_tag(self, file_id: UUID, tag: Tag):
        # Add Tags to File
        file_to_remove_tag = self._file_repository.get_by_id(file_id)
        if not file_to_remove_tag:
            raise FileNotFoundException("No file to remove tag found")
        self._task_scheduling_service.remove_tag_from_file_by_id(file_id, tag)
