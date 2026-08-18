"""Tool functions that dispatch work to Celery tasks."""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from uuid import UUID

from common.ai_context.ai_context_repository import AiContext, Capability
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
    ToolSource,
    TranslateFileResult,
)
from pydantic_ai import FunctionToolset, ModelRetry, RunContext
from pydantic_ai.exceptions import ToolFailed

from api.services.task_call_service import TaskCallService

_MAX_CITATION_CHARS = 300


@dataclass
class AgentDeps:
    context: AiContext
    source_collector: list[ToolSource] = dataclass_field(default_factory=list)
    active_capabilities: set[Capability] = dataclass_field(default_factory=set)


class ToolService:
    """Provides tool functions for the pydantic-ai agent."""

    def __init__(self, task_call_service: TaskCallService) -> None:
        self._task_call_service = task_call_service

        self.base_toolset: FunctionToolset[AgentDeps] = FunctionToolset()
        self.base_toolset.tool(self.suggest_queries)
        self.base_toolset.tool(self.get_file)
        self.base_toolset.tool(self.get_file_field)
        self.base_toolset.tool(self.summarize_file)
        self.base_toolset.tool(self.translate_file)
        self.base_toolset.tool(self.describe_image)
        self.base_toolset.tool(self.list_folder_contents)
        self.base_toolset.tool(self.search_by_filename)

        self.research_mode_toolset: FunctionToolset[AgentDeps] = FunctionToolset(
            instructions=(
                "You are in RESEARCH MODE. Take your time and perform thorough, "
                "multi-faceted research before answering. "
                "Use suggest_queries to generate precise query strings, or compose "
                "your own Lucene query when you already know the right terms. "
                "Issue multiple queries from different angles, explore promising documents "
                "in depth, and cross-reference findings across the corpus. "
                "Do not attempt to manipulate the UI in this mode — focus entirely on research."
            ),
        )
        self.research_mode_toolset.tool(self.suggest_queries)
        self.research_mode_toolset.tool(self.execute_query)
        self.research_mode_toolset.tool(self.rag_search)
        self.research_mode_toolset.tool(self.get_file)
        self.research_mode_toolset.tool(self.get_file_field)
        self.research_mode_toolset.tool(self.list_folder_contents)
        self.research_mode_toolset.tool(self.search_by_filename)

    def suggest_queries(
        self,
        ctx: RunContext[AgentDeps],
        query_description: str,
        folder_path: str | None = None,
    ) -> SuggestQueriesResult:
        """Generate ranked Lucene query candidates for a natural language description.

        Call this whenever the user wants to find or search for documents.
        Use the best-matching candidate as the query string for execute_query
        or set_search_query. The returned candidates include match counts so
        you can pick the most productive query string.

        Args:
            query_description: Natural language description of what to find.
            folder_path: Optional absolute folder path to restrict results to
                a subtree, e.g. "/" or "//source/subfolder".
        """
        try:
            return self._task_call_service.call_suggest_queries_tool(
                ctx.deps.context.id_, query_description, folder_path
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc

    def execute_query(
        self,
        ctx: RunContext[AgentDeps],
        query_string: str,
        folder_path: str | None = None,
    ) -> ExecuteQueryResult:
        """Execute a Lucene query string and return matching files with content
        snippets.

        You can use a query string returned by suggest_queries or compose your
        own Lucene query when you already know the right terms.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as
                returned by suggest_queries.
            folder_path: Optional absolute folder path to restrict results to
                a subtree, e.g. "/" or "//source/subfolder".
        """
        try:
            result = self._task_call_service.call_execute_query_tool(
                ctx.deps.context.id_, query_string, folder_path
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        ctx.deps.source_collector.extend(
            ToolSource(
                file_id=UUID(f.file_id),
                text=f.text[:_MAX_CITATION_CHARS],
            )
            for f in result.files
        )
        return result

    def get_file(self, ctx: RunContext[AgentDeps], file_id: str) -> GetFileResult:
        """Get the full path and available fields for a file by its UUID.

        Returns which fields have data so you can decide what to fetch next
        using get_file_field.

        Args:
            file_id: UUID string of the file to retrieve.
        """
        try:
            result = self._task_call_service.call_get_file_tool(
                ctx.deps.context.id_, file_id
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(ToolSource(file_id=UUID(result.file_id)))
        return result

    def get_file_field(
        self, ctx: RunContext[AgentDeps], file_id: str, field: str
    ) -> GetFileFieldResult:
        """Get the value of a specific field for a file by its UUID.

        Args:
            file_id: UUID string of the file to retrieve.
            field: Name of the field to retrieve. Use get_file to see which
                fields are available for a given file.
        """
        try:
            result = self._task_call_service.call_get_file_field_tool(
                ctx.deps.context.id_, file_id, field
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(
            ToolSource(
                file_id=UUID(result.file_id),
                text=result.value[:_MAX_CITATION_CHARS],
            )
        )
        return result

    def summarize_file(
        self, ctx: RunContext[AgentDeps], file_id: str
    ) -> SummarizeFileResult:
        """Generate an AI summary for a file and return the result.

        Blocks until summarization is complete. Call this when the user wants a
        summary generated or regenerated for a specific document.

        Args:
            file_id: UUID string of the file to summarize.
        """
        try:
            result = self._task_call_service.call_summarize_file_tool(
                ctx.deps.context.id_, file_id
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(
            ToolSource(
                file_id=UUID(result.file_id),
                text=result.summary[:_MAX_CITATION_CHARS],
            )
        )
        return result

    def translate_file(
        self, ctx: RunContext[AgentDeps], file_id: str, source_language: str
    ) -> TranslateFileResult:
        """Translate a file and return the translated text.

        Blocks until translation is complete. The translation target language is
        configured server-side. source_language is the BCP 47 / ISO 639-1 code
        of the document's current language (e.g. "de", "fr", "en").

        Args:
            file_id: UUID string of the file to translate.
            source_language: BCP 47 / ISO 639-1 language code of the document's
                current language.
        """
        try:
            result = self._task_call_service.call_translate_file_tool(
                ctx.deps.context.id_, file_id, source_language
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(
            ToolSource(
                file_id=UUID(result.file_id),
                text=result.translation[:_MAX_CITATION_CHARS],
            )
        )
        return result

    def describe_image(
        self, ctx: RunContext[AgentDeps], file_id: str
    ) -> DescribeImageResult:
        """Generate an AI description of an image file and return the result.

        Blocks until description is complete. Only has effect on image files.

        Args:
            file_id: UUID string of the image file to describe.
        """
        try:
            result = self._task_call_service.call_describe_image_tool(
                ctx.deps.context.id_, file_id
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(
            ToolSource(
                file_id=UUID(result.file_id),
                text=result.description[:_MAX_CITATION_CHARS],
            )
        )
        return result

    def list_folder_contents(
        self, ctx: RunContext[AgentDeps], folder_path: str
    ) -> ListFolderContentsResult:
        """List the direct children (subfolders and files) of a folder path.

        Returns names, types, file counts, and file IDs for each entry.
        Use "/" for the root. Use this to explore the folder structure or
        answer questions about what files exist in a given location.

        Args:
            folder_path: Absolute folder path to list, e.g. "/" or "//source/subfolder".
        """
        try:
            return self._task_call_service.call_list_folder_contents_tool(
                ctx.deps.context.id_, folder_path
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc

    def search_by_filename(
        self, ctx: RunContext[AgentDeps], filename: str
    ) -> SearchByFilenameResult:
        """Search for files whose name contains the given substring.

        Returns matching files with their full paths and IDs. Use this when
        the user asks to find a file by name rather than by content.

        Args:
            filename: Substring to match against filenames (case-insensitive).
        """
        try:
            return self._task_call_service.call_search_by_filename_tool(
                ctx.deps.context.id_, filename
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc

    def rag_search(self, ctx: RunContext[AgentDeps], query: str) -> RagSearchResult:
        """Run the full RAG pipeline: retrieve and synthesize an answer from documents.

        Args:
            query: Natural language question to answer using the document corpus.
        """
        try:
            result = self._task_call_service.call_rag_search_tool(
                ctx.deps.context.id_, query
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        ctx.deps.source_collector.extend(
            ToolSource(
                file_id=chunk.file_id,
                text=chunk.text[:_MAX_CITATION_CHARS],
            )
            for chunk in result.chunks
        )
        return result
