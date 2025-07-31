"""Service to schedule new files for processing."""

import hashlib
import logging
from pathlib import PurePath
from uuid import UUID

from bson import ObjectId

from common.file.file_repository import File, FileNotFoundException, FileRepository, Tag
from common.services.file_storage_service import FileStorageService
from common.services.lazybytes_service import LazyBytes, LazyBytesService
from common.services.task_scheduling_service import TaskSchedulingService

logger = logging.getLogger(__name__)


class FileSchedulingService:
    """Handles new files, stores them and schedules tasks."""

    def __init__(
        self,
        file_repository: FileRepository,
        file_storage_service: FileStorageService,
        task_scheduling_service: TaskSchedulingService,
        lazybytes_service: LazyBytesService,
    ):
        self._file_repository = file_repository
        self._file_storage_service = file_storage_service
        self._task_scheduling_service = task_scheduling_service
        self._lazybytes_service = lazybytes_service

    def index_file(
        self,
        full_name: str,
        file_content: LazyBytes,
        source_id: str,
        exclude_from_archives: bool = False,
    ) -> File:
        logger.info("Scheduling indexing of file: '%s'", full_name)

        # Upload to file storage, compute hash and length
        file_storage_id = ObjectId()
        file_data_hash = hashlib.sha256()
        file_len = 0
        with self._lazybytes_service.load_generator(
            file_content
        ) as file_chunk_generator, self._file_storage_service.open_upload_stream_with_id(
            file_storage_id, str(full_name)
        ) as file_upload:
            for file_chunk in file_chunk_generator:
                file_upload.write(file_chunk)
                file_data_hash.update(file_chunk)
                file_len += len(file_chunk)

        file = File(
            storage_id=str(file_storage_id),
            full_name=PurePath(full_name),
            source=source_id,
            exclude_from_archives=exclude_from_archives,
            sha256=file_data_hash.hexdigest(),
            size=file_len,
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
            self._file_storage_service.delete(file_storage_id)
            return deduplicated_file

        self._file_repository.save(file)
        self._task_scheduling_service.index_file(file, file_content)

        return file

    def reindex_file(self, file_id: UUID):
        file = self._file_repository.get_by_id(file_id)
        if file is None:
            raise FileNotFoundException("Invalid file")

        logger.info("Scheduling re-index of file '%s'", file.full_name)
        # update status
        file.state = "reindexing"
        self._file_repository.update(file, include={"state"})

        file_content = self._lazybytes_service.from_generator(
            self._file_storage_service.open_download_iterator(
                file_id=ObjectId(file.storage_id)
            )
        )
        self._task_scheduling_service.index_file(file, file_content)

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

    def set_hidden_state(self, file_id: UUID, hidden: bool):
        file_to_hide = self._file_repository.get_by_id(file_id)
        if not file_to_hide:
            raise FileNotFoundException("No file to hide found")
        if hidden:
            file_to_hide.state = "hiding"
        else:
            file_to_hide.state = "showing"

        self._file_repository.update(file_to_hide, include={"state"})
        self._task_scheduling_service.set_hidden_state_by_id(file_id, hidden)

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
