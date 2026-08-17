"""Synchronous task dispatch service for API-side tool calls."""

from uuid import UUID, uuid4

from common.ai_context.tool_models import (
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
)
from common.file.file_repository import TranslatedLanguage
from common.services.task_service import TaskService

_TASK_TIMEOUT = 300


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
        ).get(timeout=_TASK_TIMEOUT)
        return SuggestQueriesResult.model_validate(result)

    def call_execute_query_tool(
        self,
        context_id: UUID,
        query_string: str,
        folder_path: str | None = None,
    ) -> ExecuteQueryResult:
        result = self._send_task(
            "worker.ai.tasks.execute_query_tool.execute_query_tool_task",
            args=[query_string, context_id, folder_path],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return ExecuteQueryResult.model_validate(result)

    def call_list_folder_contents_tool(
        self, context_id: UUID, folder_path: str
    ) -> ListFolderContentsResult:
        result = self._send_task(
            "worker.ai.tasks.list_folder_contents_tool.list_folder_contents_tool_task",
            args=[folder_path, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return ListFolderContentsResult.model_validate(result)

    def call_search_by_filename_tool(
        self, context_id: UUID, filename: str
    ) -> SearchByFilenameResult:
        result = self._send_task(
            "worker.ai.tasks.search_by_filename_tool.search_by_filename_tool_task",
            args=[filename, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return SearchByFilenameResult.model_validate(result)

    def call_get_file_tool(self, context_id: UUID, file_id: str) -> GetFileResult:
        result = self._send_task(
            "worker.ai.tasks.get_file_tool.get_file_tool_task",
            args=[file_id, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return GetFileResult.model_validate(result)

    def call_get_file_field_tool(
        self, context_id: UUID, file_id: str, field: str
    ) -> GetFileFieldResult:
        result = self._send_task(
            "worker.ai.tasks.get_file_tool.get_file_field_tool_task",
            args=[file_id, field, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return GetFileFieldResult.model_validate(result)

    def call_rag_search_tool(self, context_id: UUID, query: str) -> RagSearchResult:
        result = self._send_task(
            "worker.ai.tasks.rag_tool.rag_search_tool_task",
            args=[query, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return RagSearchResult.model_validate(result)

    def call_summarize_file_tool(
        self, context_id: UUID, file_id: str
    ) -> SummarizeFileResult:
        result = self._send_task(
            "worker.ai.tasks.summarize_file_tool.summarize_file_tool_task",
            args=[file_id, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
        return SummarizeFileResult(file_id=file_id, summary=result or "")

    def call_translate_file_tool(
        self, context_id: UUID, file_id: str, source_language: str
    ) -> TranslateFileResult:
        result = self._send_task(
            "worker.ai.tasks.translate_file_tool.translate_file_tool_task",
            args=[file_id, source_language, context_id],
            root_id=str(uuid4()),
        ).get(timeout=_TASK_TIMEOUT)
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
        ).get(timeout=_TASK_TIMEOUT)
        return DescribeImageResult(file_id=file_id, description=result or "")
