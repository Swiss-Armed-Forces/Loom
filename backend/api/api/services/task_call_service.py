"""Synchronous task dispatch service for API-side tool calls."""

from uuid import UUID, uuid4

from common.ai_context.tool_models import (
    AddTagsToFileResult,
    DescribeImageResult,
    ExecuteQueryResult,
    GetFileFieldResult,
    GetFileResult,
    ListFolderContentsResult,
    RagSearchResult,
    SearchByFilenameResult,
    SuggestQueriesResult,
    SummarizeFileResult,
    TranslateFileResult,
    UpdateFileResult,
)
from common.file.file_repository import Tag, TranslatedLanguage
from common.models.cursor_pagination import SearchAfterCursor
from common.services.task_scheduling_service import UpdateFileRequest
from common.services.task_service import TaskService


class TaskCallService(TaskService):
    """Dispatches single worker tasks and blocks until their result is available."""

    def call_suggest_queries_tool(
        self,
        context_id: UUID,
        query_description: str,
        folder_path: str | None = None,
    ) -> SuggestQueriesResult:
        result = self._send_task(
            "worker.ai.tasks.suggest_queries_tool.suggest_queries_task",
            args=[query_description, context_id, folder_path],
            root_id=str(uuid4()),
        ).get()
        return SuggestQueriesResult.model_validate(result)

    def call_execute_query_tool(
        self,
        context_id: UUID,
        query_string: str,
        folder_path: str | None = None,
        after_cursor: SearchAfterCursor | None = None,
    ) -> ExecuteQueryResult:
        result = self._send_task(
            "worker.ai.tasks.execute_query_tool.execute_query_tool_task",
            args=[query_string, context_id, folder_path, after_cursor],
            root_id=str(uuid4()),
        ).get()
        return ExecuteQueryResult.model_validate(result)

    def call_list_folder_contents_tool(
        self,
        context_id: UUID,
        folder_path: str,
        after_cursor: SearchAfterCursor | None = None,
    ) -> ListFolderContentsResult:
        result = self._send_task(
            "worker.ai.tasks.list_folder_contents_tool.list_folder_contents_tool_task",
            args=[folder_path, context_id, after_cursor],
            root_id=str(uuid4()),
        ).get()
        return ListFolderContentsResult.model_validate(result)

    def call_search_by_filename_tool(
        self,
        context_id: UUID,
        filename: str,
        search_string: str = "*",
        after_cursor: SearchAfterCursor | None = None,
    ) -> SearchByFilenameResult:
        result = self._send_task(
            "worker.ai.tasks.search_by_filename_tool.search_by_filename_tool_task",
            args=[filename, context_id, search_string, after_cursor],
            root_id=str(uuid4()),
        ).get()
        return SearchByFilenameResult.model_validate(result)

    def call_get_file_tool(self, context_id: UUID, file_id: str) -> GetFileResult:
        result = self._send_task(
            "worker.ai.tasks.get_file_tool.get_file_tool_task",
            args=[file_id, context_id],
            root_id=str(uuid4()),
        ).get()
        return GetFileResult.model_validate(result)

    def call_get_file_field_tool(
        self, context_id: UUID, file_id: str, field: str
    ) -> GetFileFieldResult:
        result = self._send_task(
            "worker.ai.tasks.get_file_tool.get_file_field_tool_task",
            args=[file_id, field, context_id],
            root_id=str(uuid4()),
        ).get()
        return GetFileFieldResult.model_validate(result)

    def call_rag_search_tool(self, context_id: UUID, query: str) -> RagSearchResult:
        result = self._send_task(
            "worker.ai.tasks.rag_tool.rag_search_tool_task",
            args=[query, context_id],
            root_id=str(uuid4()),
        ).get()
        return RagSearchResult.model_validate(result)

    def call_summarize_file_tool(
        self, context_id: UUID, file_id: str
    ) -> SummarizeFileResult:
        result = self._send_task(
            "worker.ai.tasks.summarize_file_tool.summarize_file_tool_task",
            args=[file_id, context_id],
            root_id=str(uuid4()),
        ).get()
        return SummarizeFileResult(file_id=file_id, summary=result or "")

    def call_translate_file_tool(
        self, context_id: UUID, file_id: str, source_language: str
    ) -> TranslateFileResult:
        result = self._send_task(
            "worker.ai.tasks.translate_file_tool.translate_file_tool_task",
            args=[file_id, source_language, context_id],
            root_id=str(uuid4()),
        ).get()
        translation = (
            TranslatedLanguage.model_validate(result[0]).text if result else ""
        )
        return TranslateFileResult(
            file_id=file_id, source_language=source_language, translation=translation
        )

    def call_describe_image_tool(
        self, context_id: UUID, file_id: str
    ) -> DescribeImageResult:
        result = self._send_task(
            "worker.ai.tasks.describe_image_tool.describe_image_tool_task",
            args=[file_id, context_id],
            root_id=str(uuid4()),
        ).get()
        return DescribeImageResult(file_id=file_id, description=result or "")

    def call_add_tags_to_file_tool(
        self, context_id: UUID, file_id: str, tags: list[Tag]
    ) -> AddTagsToFileResult:
        result = self._send_task(
            "worker.ai.tasks.add_tags_to_file_tool.add_tags_to_file_tool_task",
            args=[file_id, tags, context_id],
            root_id=str(uuid4()),
        ).get()
        return AddTagsToFileResult(file_id=file_id, tags_added=list(result or []))

    def call_update_file_tool(
        self, context_id: UUID, file_id: str, request: UpdateFileRequest
    ) -> UpdateFileResult:
        result = self._send_task(
            "worker.ai.tasks.update_file_tool.update_file_tool_task",
            args=[file_id, request, context_id],
            root_id=str(uuid4()),
        ).get()
        applied = UpdateFileRequest.model_validate(result or {})
        return UpdateFileResult(file_id=file_id, **applied.model_dump())
