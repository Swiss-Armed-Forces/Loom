"""Tool functions that dispatch work to Celery tasks."""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import NamedTuple
from uuid import UUID

from ag_ui.core import Tool as AGUITool
from common.ai_context.ai_context_repository import AiContext, CapabilityId, ModeId
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
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.capabilities import Capability
from pydantic_ai.exceptions import ToolFailed
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets import ExternalToolset

from api.services.task_call_service import TaskCallService

_MAX_CITATION_CHARS = 300


@dataclass
class AgentDeps:
    context: AiContext
    source_collector: list[ToolSource] = dataclass_field(default_factory=list)
    active_mode: ModeId = ModeId.WORK


class RoutedTools(NamedTuple):
    always_on: list[AGUITool]
    capabilities: list[Capability[AgentDeps]]


class ToolService:
    """Provides tool functions for the pydantic-ai agent."""

    def __init__(self, task_call_service: TaskCallService) -> None:
        self._task_call_service = task_call_service

        self._search_and_browse = Capability[AgentDeps](
            id=CapabilityId.SEARCH_AND_BROWSE,
            description=(
                "Search the document corpus by content or filename "
                "and browse the folder structure."
            ),
            instructions=(
                "Start broad, then narrow down. Generate query candidates "
                "before executing searches, and explore the folder tree "
                "to orient yourself in the corpus."
            ),
            tools=[
                self.suggest_queries,
                self.list_folder_contents,
                self.search_by_filename,
            ],
            defer_loading=True,
        )

        self._file_access = Capability[AgentDeps](
            id=CapabilityId.FILE_ACCESS,
            description=(
                "Access individual files — identify which files the user "
                "is looking at, retrieve metadata, and read specific fields."
            ),
            instructions=(
                "Always confirm a file exists before reading its fields. "
                "When the user refers to 'this file' or 'these files', "
                "resolve the reference through the UI context first."
            ),
            tools=[self.get_file, self.get_file_field],
            defer_loading=True,
        )

        self._ai_processing = Capability[AgentDeps](
            id=CapabilityId.AI_PROCESSING,
            description=(
                "AI-powered file processing — generate summaries, "
                "translate content, and describe images."
            ),
            instructions=(
                "Use these to enrich documents with AI-generated content "
                "whenever it would help answer the user's question."
            ),
            tools=[self.summarize_file, self.translate_file, self.describe_image],
            defer_loading=True,
        )

        self._ui_interaction = Capability[AgentDeps](
            id=CapabilityId.UI_INTERACTION,
            description=(
                "Control what the user sees. Load this whenever the user "
                "asks you to show, open, navigate, search, filter, tag, "
                "or change anything in the UI."
            ),
            instructions=(
                "The user is interacting with you through a document search UI. "
                "When they make imperative requests, act on them directly "
                "through the UI rather than just describing what to do."
            ),
            defer_loading=True,
        )

        self._research = Capability[AgentDeps](
            id=CapabilityId.RESEARCH,
            description=(
                "Deep document research — query the corpus directly "
                "and synthesize answers from multiple sources."
            ),
            instructions=(
                "You are in RESEARCH MODE. Take your time and perform thorough, "
                "multi-faceted research before answering. "
                "Issue multiple queries from different angles, explore promising "
                "documents in depth, and cross-reference findings across the corpus. "
                "Do not attempt to manipulate the UI in this mode — focus entirely "
                "on research."
            ),
            tools=[self.execute_query, self.rag_search],
        )

    def capabilities_for_mode(self, mode: ModeId) -> list[Capability[AgentDeps]]:
        """Return the capabilities available for the given mode."""
        match mode:
            case ModeId.CHAT:
                return []
            case ModeId.RESEARCH:
                return [
                    self._search_and_browse,
                    self._file_access,
                    self._ai_processing,
                    self._research,
                ]
            case _:
                return [
                    self._search_and_browse,
                    self._file_access,
                    self._ai_processing,
                    self._ui_interaction,
                ]

    def route_frontend_tools(
        self,
        tools: list[AGUITool],
        base_capabilities: list[Capability[AgentDeps]],
    ) -> RoutedTools:
        """Partition frontend tools into always-on and capability-gated groups.

        Each frontend tool may declare a ``capability`` field matching a deferred
        capability ID.  Tools with a matching capability are routed into rebuilt
        ``Capability`` instances alongside their backend tools. Tools without a
        capability stay always-on.
        """
        always_on: list[AGUITool] = []
        by_capability: dict[CapabilityId, list[ToolDefinition]] = {}

        for tool in tools:
            raw_ids = (tool.model_extra or {}).get("capabilities") or []
            matched = [
                CapabilityId(c)
                for c in raw_ids
                if c in CapabilityId.__members__.values()
            ]
            if not matched:
                always_on.append(tool)
            else:
                tool_def = ToolDefinition(
                    name=tool.name,
                    description=tool.description or "",
                    parameters_json_schema=tool.parameters or {},
                    kind="external",
                )
                for cap_id in matched:
                    by_capability.setdefault(cap_id, []).append(tool_def)

        capabilities: list[Capability[AgentDeps]] = []
        for cap in base_capabilities:
            raw_id = cap.id
            if raw_id is None or raw_id not in CapabilityId.__members__.values():
                capabilities.append(cap)
                continue
            cap_id = CapabilityId(raw_id)
            frontend_defs = by_capability.get(cap_id)
            if frontend_defs is None:
                capabilities.append(cap)
            else:
                capabilities.append(
                    Capability[AgentDeps](
                        id=cap.id,
                        description=cap.description,
                        instructions=(  # pylint: disable=protected-access
                            cap._instructions[0] if cap._instructions else None
                        ),
                        tools=list(cap.tools),
                        toolsets=[ExternalToolset(tool_defs=frontend_defs)],
                        defer_loading=cap.defer_loading,
                    )
                )

        return RoutedTools(always_on=always_on, capabilities=capabilities)

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
            result = self._task_call_service.call_search_by_filename_tool(
                ctx.deps.context.id_, filename
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        ctx.deps.source_collector.extend(
            ToolSource(
                file_id=UUID(f.file_id),
                text=f.full_path,
            )
            for f in result.files
        )
        return result

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
