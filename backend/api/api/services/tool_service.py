"""Tool functions that dispatch work to Celery tasks."""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from uuid import UUID

from common.ai_context.ai_context_repository import AiContext, CapabilityId
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
from common.file.file_repository import FileRepository
from common.services.query_builder import QueryBuilderException, QueryParameters
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.capabilities import AgentCapability, Capability
from pydantic_ai.exceptions import ToolFailed
from pydantic_ai.messages import ToolCallPart

from api.services.task_call_service import TaskCallService

ToolCallValidatorFn = Callable[["RunContext[AgentDeps]", ToolCallPart], ToolCallPart]

_ValidatorMethod = Callable[..., ToolCallPart]  # unbound method including self

_validator_registry: dict[str, str] = {}


def _validates(tool_name: str) -> Callable[[_ValidatorMethod], _ValidatorMethod]:
    """Register a method as a validator for the given deferred tool name."""

    def decorator(fn: _ValidatorMethod) -> _ValidatorMethod:
        _validator_registry[tool_name] = fn.__name__
        return fn

    return decorator


_MAX_CITATION_CHARS = 300


@dataclass
class AgentDeps:
    context: AiContext
    source_collector: list[ToolSource] = dataclass_field(default_factory=list)
    active_capabilities: set[CapabilityId] = dataclass_field(default_factory=set)


class ToolService:
    """Provides tool functions for the pydantic-ai agent."""

    def __init__(
        self,
        task_call_service: TaskCallService,
        file_repository: FileRepository,
    ) -> None:
        self._task_call_service = task_call_service
        self._file_repository = file_repository

        self._search_and_browse = Capability[AgentDeps](
            id="search_and_browse",
            description=(
                "Tools for searching documents by content or filename "
                "and browsing the folder structure."
            ),
            tools=[
                self.suggest_queries,
                self.list_folder_contents,
                self.search_by_filename,
            ],
            defer_loading=True,
        )

        self._file_access = Capability[AgentDeps](
            id="file_access",
            description=(
                "Tools for retrieving file metadata and reading "
                "individual file fields."
            ),
            tools=[self.get_file, self.get_file_field],
            defer_loading=True,
        )

        self._ai_processing = Capability[AgentDeps](
            id="ai_processing",
            description=(
                "Tools for AI-powered file processing: summarization, "
                "translation, and image description."
            ),
            tools=[self.summarize_file, self.translate_file, self.describe_image],
            defer_loading=True,
        )

        self._ui_interaction = Capability[AgentDeps](
            id="ui_interaction",
            instructions=(
                "The user is interacting with you through a document search UI. "
                "When the user wants to find or search for documents, after "
                "generating query candidates with suggest_queries, use "
                "set_search_query to apply the query and update the search view."
            ),
        )

        self._research_mode = Capability[AgentDeps](
            id="research_mode",
            instructions=(
                "You are in RESEARCH MODE. Take your time and perform thorough, "
                "multi-faceted research before answering. "
                "Use suggest_queries to generate precise query strings, or compose "
                "your own Lucene query when you already know the right terms. "
                "Issue multiple queries from different angles, explore promising documents "
                "in depth, and cross-reference findings across the corpus. "
                "Do not attempt to manipulate the UI in this mode — focus entirely on research."
            ),
            tools=[self.execute_query, self.rag_search],
        )

    @property
    def capabilities(self) -> list[AgentCapability[AgentDeps]]:
        """All capabilities for the agent, including the dynamic research mode."""

        def _ui_interaction_fn(
            ctx: RunContext[AgentDeps],
        ) -> Capability[AgentDeps] | None:
            if CapabilityId.RESEARCH_MODE not in ctx.deps.active_capabilities:
                return self._ui_interaction
            return None

        def _research_mode_fn(
            ctx: RunContext[AgentDeps],
        ) -> Capability[AgentDeps] | None:
            if CapabilityId.RESEARCH_MODE in ctx.deps.active_capabilities:
                return self._research_mode
            return None

        return [
            self._search_and_browse,
            self._file_access,
            self._ai_processing,
            _ui_interaction_fn,
            _research_mode_fn,
        ]

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

    @property
    def tool_call_validators(self) -> dict[str, ToolCallValidatorFn]:
        return {
            tool_name: getattr(self, method_name)
            for tool_name, method_name in _validator_registry.items()
        }

    @_validates("set_search_query")
    def _validate_set_search_query(
        self, _ctx: RunContext[AgentDeps], call: ToolCallPart
    ) -> ToolCallPart:
        args = call.args_as_dict()
        query_string = args.get("query", "")
        if not query_string:
            return call
        try:
            count = self._file_repository.count_by_query(
                QueryParameters(search_string=query_string)
            )
        except QueryBuilderException as exc:
            raise ModelRetry(
                f"The search query {query_string!r} has invalid syntax: {exc}. "
                "Use suggest_queries to generate a valid query string."
            ) from exc
        if count == 0:
            raise ModelRetry(
                f"The search query {query_string!r} returned no results. "
                "Use suggest_queries to generate a query that matches documents."
            )
        return call
