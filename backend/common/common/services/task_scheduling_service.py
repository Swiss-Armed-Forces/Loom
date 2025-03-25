"""Provides a service for scheduling tasks to be executed by the worker."""

from uuid import UUID, uuid4

from celery import Celery

from common.ai_context.ai_context_repository import AiContext
from common.archive.archive_repository import Archive
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from common.task_object.root_task_information_repository import (
    RootTaskInformation,
    RootTaskInformationRepository,
)


class TaskSchedulingService:
    """Schedules tasks to be executed by the worker."""

    def __init__(
        self,
        celery_app: Celery,
        root_task_information_repository: RootTaskInformationRepository,
    ):
        self._celery_app = celery_app
        self._root_task_information_repository = root_task_information_repository

    def create_archive(self, archive: Archive):
        """Schedule the creation of an archive."""
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=archive.root_task_id,
                object_id=archive.id_,
            )
        )
        self._celery_app.send_task(
            "worker.create_archive.create_archive_task.create_archive_task",
            args=[archive],
            task_id=str(archive.root_task_id),
            root_id=str(archive.root_task_id),
        ).forget()

    def dispatch_reindex_files(self, query: QueryParameters):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.index_file_task.dispatch_reindex_files",
            args=[query],
            root_id=str(root_task_id),
        ).forget()

    def index_file(self, file: File, file_content: LazyBytes):
        """Schedule the indexing of a file."""
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=file.root_task_id,
                object_id=file.id_,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.index_file_task.index_file_task",
            args=[file, file_content],
            task_id=str(file.root_task_id),
            root_id=str(file.root_task_id),
        ).forget()

    def dispatch_translate_files(self, query: QueryParameters, lang: str):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.translate_file_task.dispatch_translate_files",
            args=[query, lang],
            root_id=str(root_task_id),
        ).forget()

    def translate_files_by_id(self, file_id: UUID, lang: str):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=file_id,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.translate_file_task.translate_file_task",
            args=[lang, file_id],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()

    def dispatch_summarize_files(
        self, query: QueryParameters, system_prompt: str | None = None
    ):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.summarize_file_task.dispatch_summarize_files",
            args=[query, system_prompt],
            root_id=str(root_task_id),
        ).forget()

    def summarize_files_by_id(self, file_id: UUID, system_prompt: str | None = None):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=file_id,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.summarize_file_task.summarize_file_task",
            args=[file_id, system_prompt],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()

    def dispatch_set_hidden_state(self, query: QueryParameters, hidden: bool):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.set_hidden_state_task.dispatch_set_hidden_state_for_files",
            args=[query, hidden],
            root_id=str(root_task_id),
        ).forget()

    def set_hidden_state_by_id(self, file_id: UUID, hidden: bool):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=file_id,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.set_hidden_state_task.set_hidden_state_task",
            args=[file_id, hidden],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()

    def dispatch_add_tags(self, query: QueryParameters, tags: list[str]):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.add_tags_to_file_task.dispatch_add_tags_to_files",
            args=[query, tags],
            root_id=str(root_task_id),
        ).forget()

    def add_tag_to_file_by_id(self, file_id: UUID, tags: list[str]):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=file_id,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.add_tags_to_file_task.add_tags_to_file_task",
            args=[file_id, tags],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()

    def dispatch_remove_tag(self, tag):
        root_task_id = uuid4()
        self._celery_app.send_task(
            "worker.index_file.remove_tag_from_file_task.dispatch_remove_tag",
            args=[tag],
            root_id=str(root_task_id),
        ).forget()

    def remove_tag_from_file_by_id(self, file_id: UUID, tag: str):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=file_id,
            )
        )
        self._celery_app.send_task(
            "worker.index_file.remove_tag_from_file_task.remove_tag_from_file_task",
            args=[file_id, tag],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()

    def ai_process_question(self, context: AiContext, question: str):
        root_task_id = uuid4()
        self._root_task_information_repository.save(
            RootTaskInformation(
                root_task_id=root_task_id,
                object_id=context.id_,
            )
        )
        self._celery_app.send_task(
            "worker.ai.process_question_task.process_question_task",
            args=[context, question],
            task_id=str(root_task_id),
            root_id=str(root_task_id),
        ).forget()
