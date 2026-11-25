"""Tool functions that dispatch work to Celery tasks."""

import secrets
from typing import NamedTuple
from uuid import UUID

from ag_ui.core import BaseEvent, CustomEvent
from ag_ui.core import Tool as AGUITool
from common.ai_context.ai_context_repository import (
    CapabilityId,
    ModeId,
)
from common.ai_context.tool_models import (
    AddTagsToFileResult,
    CursorHandle,
    DescribeImageResult,
    ExecuteQueryAgentResult,
    ListFolderContentsAgentResult,
    RagSearchResult,
    SearchByFilenameAgentResult,
    SuggestQueriesResult,
    SummarizeFileResult,
    ToolSource,
    TranslateFileResult,
    UpdateFileResult,
)
from common.file.file_repository import Tags
from common.models.cursor_pagination import CursorSource, SearchAfterCursor
from common.services.query_builder import AI_PIT_KEEPALIVE, convert_keepalive_to_seconds
from common.services.task_scheduling_service import UpdateFileRequest
from common.settings import settings
from pydantic_ai import ModelRetry, RunContext, ToolReturn
from pydantic_ai.capabilities import Capability
from pydantic_ai.exceptions import ToolFailed
from pydantic_ai.tools import Tool as PydanticTool
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets import ExternalToolset
from redis import StrictRedis

from api.services.agent_deps import AgentDeps
from api.services.bulk_tool_service import (
    APPROVAL_INSTRUCTIONS,
    BulkToolService,
)
from api.services.task_call_service import TaskCallService

_MAX_CITATION_CHARS = 300

# What each mode may load, in the order the agent is offered them. Research reaches
# the whole corpus and composes its own queries with no user in the loop, which is why
# the capability that acts on files is work-mode only.
_RESEARCH_CAPABILITIES = (
    CapabilityId.SEARCH_AND_BROWSE,
    CapabilityId.RESEARCH,
)
_WORK_CAPABILITIES = (
    CapabilityId.SEARCH_AND_BROWSE,
    CapabilityId.ENRICHMENT,
    CapabilityId.UI_INTERACTION,
)

# Events the frontend applies to the results list and the highlight. They ride on the
# tool return rather than on a collector drained after the run, so the user's screen
# moves while the agent is still working.
_SET_SEARCH_QUERY_EVENT = "set_search_query"
_HIGHLIGHT_FILE_EVENT = "highlight_file"


class RoutedTools(NamedTuple):
    always_on: list[AGUITool]
    capabilities: list[Capability[AgentDeps]]


class ToolService:
    """Provides tool functions for the pydantic-ai agent."""

    def __init__(
        self,
        task_call_service: TaskCallService,
        redis_cache_client: StrictRedis,
        bulk_tool_service: BulkToolService,
    ) -> None:
        self._task_call_service = task_call_service
        self._redis_client = redis_cache_client

        t = settings.llm.agent.tool_timeout

        research = Capability[AgentDeps](
            id=CapabilityId.RESEARCH,
            description=(
                "Deep document research — query the corpus directly "
                "and synthesize answers from multiple sources."
            ),
            instructions=(
                "Take your time and perform thorough, multi-faceted research "
                "before answering. Issue multiple queries from different angles, "
                "explore promising documents in depth, and cross-reference "
                "findings across the corpus."
            ),
            tools=[PydanticTool(self.rag_search, timeout=t)],
            defer_loading=True,
        )

        enrichment = Capability[AgentDeps](
            id=CapabilityId.ENRICHMENT,
            description=(
                "Change files: generate summaries, translations and image "
                "descriptions, add tags, and set the seen, flagged and hidden "
                "state — for one file or for every file a query matches."
            ),
            instructions=(
                APPROVAL_INSTRUCTIONS
                + "These tools differ enormously in reach, so read the name before "
                "calling one. The per-file AI tools cost inference time and nothing "
                "else. add_tags_to_file and update_file land immediately, have no "
                "undo and are not put to the user, so say which file you are about to "
                "change and what you are setting on it; curating a handful of files "
                "one call at a time is normal. A bulk_ call queues work across a whole "
                "query: bulk_summarize, bulk_translate and bulk_describe_images spend "
                "one model call per matched file on the same inference server you are "
                "running on, so a large sweep takes hours — report that the work is "
                "queued, never that it is done. bulk_add_tags and bulk_update_files "
                "write immediately and cannot be taken back, so use the narrowest "
                "query that covers what the user asked for and check it with "
                "execute_query when you are unsure what it matches."
            ),
            tools=[
                PydanticTool(self.summarize_file, timeout=t),
                PydanticTool(self.translate_file, timeout=t),
                PydanticTool(self.describe_image, timeout=t),
                PydanticTool(self.add_tags_to_file, timeout=t),
                PydanticTool(self.update_file, timeout=t),
                *bulk_tool_service.tools,
            ],
            defer_loading=True,
        )

        ui_interaction = Capability[AgentDeps](
            id=CapabilityId.UI_INTERACTION,
            description=(
                "See and control the user's UI. Load this whenever the user "
                "references what they are currently seeing, or asks you to "
                "show, open, navigate, filter or change anything in the UI."
            ),
            instructions=(
                "The user is interacting with you through a document search UI. "
                "When they reference their screen, read the UI state to understand "
                "their context. When they make imperative requests, act on them "
                "directly through the UI rather than just describing what to do."
            ),
            defer_loading=True,
        )

        self._capabilities: dict[CapabilityId, Capability[AgentDeps]] = {
            CapabilityId.RESEARCH: research,
            CapabilityId.ENRICHMENT: enrichment,
            CapabilityId.UI_INTERACTION: ui_interaction,
        }
        # One bundle, two descriptions: the tools are identical in both modes but two
        # of them drive the user's screen in work mode, and a capability's description
        # and instructions are the only place the agent can be told so.
        self._search_and_browse: dict[ModeId, Capability[AgentDeps]] = {
            ModeId.RESEARCH: self._build_search_and_browse(t, drives_ui=False),
            ModeId.WORK: self._build_search_and_browse(t, drives_ui=True),
        }

    def _build_search_and_browse(
        self, timeout: int | None, *, drives_ui: bool
    ) -> Capability[AgentDeps]:
        """The read bundle, told whether its two UI-driving tools are live."""
        drives_ui_note = (
            " execute_query also applies the query to the user's results list, and "
            "get_file and get_file_field both highlight the file they read, so what "
            "you read is what the user is looking at. suggest_queries, "
            "search_by_filename and list_folder_contents leave the screen alone."
            if drives_ui
            else ""
        )
        return Capability[AgentDeps](
            id=CapabilityId.SEARCH_AND_BROWSE,
            description=(
                "Read the document corpus: turn a description into a query, run it, "
                "search by filename, browse the folder structure, and read the "
                "fields of a single file."
            ),
            instructions=(
                "Start broad, then narrow down. Generate query candidates with "
                "suggest_queries before executing searches, and explore the folder "
                "tree to orient yourself in the corpus. Results are paginated: "
                "compare what you have actually read against total_count before "
                "describing a result set, and never characterise the matches from "
                "the hits you have seen. A large total_count means the query is too "
                "broad — partition it into several narrower queries and compare "
                "their counts rather than paging through one." + drives_ui_note
            ),
            tools=[
                PydanticTool(self.suggest_queries, timeout=timeout),
                PydanticTool(self.execute_query, timeout=timeout),
                PydanticTool(self.search_by_filename, timeout=timeout),
                PydanticTool(self.list_folder_contents, timeout=timeout),
                PydanticTool(self.get_file, timeout=timeout),
                PydanticTool(self.get_file_field, timeout=timeout),
            ],
            defer_loading=True,
        )

    def _ui_effect(
        self, ctx: RunContext[AgentDeps], name: str, value: dict[str, str]
    ) -> list[BaseEvent]:
        """The frontend events a read should cause, which is none outside work mode."""
        if ctx.deps.context.active_mode is not ModeId.WORK:
            return []
        return [CustomEvent(name=name, value=value)]

    def _store_cursor(self, cursor: SearchAfterCursor | None) -> CursorHandle | None:
        """Keep a cursor in the run's state and return the handle that names it.

        The cursor carries a point-in-time id that is both long and of no use to the
        agent, which would otherwise pay for it twice per page — once reading it, once
        passing it back.
        """
        if cursor is None:
            return None
        handle = CursorHandle(secrets.token_urlsafe(16))

        self._redis_client.hset(
            f"aipitmap:{handle}", "cursor", cursor.model_dump_json()
        )
        self._redis_client.expire(
            f"aipitmap:{handle}", convert_keepalive_to_seconds(AI_PIT_KEEPALIVE)
        )

        return handle

    def _resolve_cursor(
        self,
        handle: CursorHandle | None,
        expected_src: CursorSource,
    ) -> SearchAfterCursor | None:
        if handle is None:
            return None

        raw_cursor = self._redis_client.hget(f"aipitmap:{handle}", "cursor")

        if raw_cursor is None:
            raise ModelRetry(
                "Unknown after_cursor. Cursors are only valid within the "
                "run that produced them, and only the most recent ones are kept. "
                "Call this tool again without after_cursor to start from the "
                "first page."
            )

        cursor = SearchAfterCursor.model_validate_json(raw_cursor)

        # The worker rejects a cursor from another search as well, but it is the agent
        # confusing two tools that this catches, and there is no reason to spend a task
        # round-trip on finding that out.
        if cursor.src != expected_src:
            raise ModelRetry(
                "That after_cursor belongs to a different tool. Pass a cursor back "
                "only to the tool that returned it, or omit it to start from the "
                "first page."
            )
        return cursor

    def capabilities_for_mode(self, mode: ModeId) -> list[Capability[AgentDeps]]:
        """Return the capabilities available for the given mode."""
        match mode:
            case ModeId.CHAT:
                capability_ids: tuple[CapabilityId, ...] = ()
            case ModeId.RESEARCH:
                capability_ids = _RESEARCH_CAPABILITIES
            # Spelled out rather than caught by a fallthrough: enrichment writes across
            # a whole query with no undo, and a mode added to the enum must not inherit
            # it by default.
            case ModeId.WORK:
                capability_ids = _WORK_CAPABILITIES
        return [
            self._capability_for(capability_id, mode)
            for capability_id in capability_ids
        ]

    def _capability_for(
        self, capability_id: CapabilityId, mode: ModeId
    ) -> Capability[AgentDeps]:
        if capability_id is CapabilityId.SEARCH_AND_BROWSE:
            return self._search_and_browse[mode]
        return self._capabilities[capability_id]

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
                        instructions=cap.get_instructions(),
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
        after_cursor: CursorHandle | None = None,
    ) -> ToolReturn:
        """Execute a Lucene query string and return matching files with content
        snippets.

        In work mode this also applies the query to the user's results list, so what
        you read is what they are looking at.

        You can use a query string returned by suggest_queries or compose your
        own Lucene query when you already know the right terms.

        Results are paginated, best matches first. The response includes
        total_count, count_relation, has_more, and next_cursor. When has_more is True,
        call this tool again with the same query_string and folder_path, and
        the returned next_cursor as after_cursor, to retrieve the next page.
        Count_relation is set to "eq" if the total_count is exact. If set to "gte"
        the total_count is a lower bound.

        Args:
            query_string: A valid Elasticsearch Lucene query string, as
                returned by suggest_queries.
            folder_path: Optional absolute folder path to restrict results to
                a subtree, e.g. "/" or "//source/subfolder". Must be repeated
                unchanged when paging.
            after_cursor: Opaque pagination cursor from a previous call's
                next_cursor field. Cursors belong to the tool that produced
                them; do not pass one from a different tool. Omit for the
                first page.
        """
        resolved_cursor = self._resolve_cursor(after_cursor, "execute_query")
        try:
            result = self._task_call_service.call_execute_query_tool(
                ctx.deps.context.id_,
                query_string,
                folder_path,
                resolved_cursor,
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
        return ToolReturn(
            return_value=ExecuteQueryAgentResult.from_tool_result(
                result, self._store_cursor(result.next_cursor)
            ),
            metadata=self._ui_effect(
                ctx, _SET_SEARCH_QUERY_EVENT, {"query": query_string}
            ),
        )

    def get_file(self, ctx: RunContext[AgentDeps], file_id: str) -> ToolReturn:
        """Get the full path and available fields for a file by its UUID.

        Returns which fields have data so you can decide what to fetch next
        using get_file_field. In work mode this also highlights the file in the
        user's results list.

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
        return ToolReturn(
            return_value=result,
            metadata=self._ui_effect(
                ctx, _HIGHLIGHT_FILE_EVENT, {"file_id": result.file_id}
            ),
        )

    def get_file_field(
        self, ctx: RunContext[AgentDeps], file_id: str, field: str
    ) -> ToolReturn:
        """Get the value of a specific field for a file by its UUID.

        Long fields are capped. When the response has truncated set to True, value
        holds only the leading characters of the field and the rest cannot be
        reached through this tool — use summarize_file to cover the whole document,
        or execute_query to find the passages that matter. Do not answer as though
        a truncated value were the complete field.

        In work mode this also highlights the file in the user's results list.

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
        return ToolReturn(
            return_value=result,
            metadata=self._ui_effect(
                ctx, _HIGHLIGHT_FILE_EVENT, {"file_id": result.file_id}
            ),
        )

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
        self,
        ctx: RunContext[AgentDeps],
        folder_path: str,
        after_cursor: CursorHandle | None = None,
    ) -> ListFolderContentsAgentResult:
        """List the direct children (subfolders and files) of a folder path.

        Returns names, types, file counts, and file IDs for each entry.
        Use "/" for the root. Use this to explore the folder structure or
        answer questions about what files exist in a given location.

        Results are paginated. The response includes has_more and next_cursor.
        When has_more is True, call this tool again with the same folder_path
        and the returned next_cursor as after_cursor to retrieve the next page.

        Args:
            folder_path: Absolute folder path to list, e.g. "/" or "//source/subfolder".
            after_cursor: Opaque pagination cursor from a previous call's
                next_cursor field. Cursors belong to the tool that produced
                them; do not pass one from a different tool. Omit for the
                first page.
        """
        resolved_cursor = self._resolve_cursor(after_cursor, "list_folder_contents")
        try:
            result = self._task_call_service.call_list_folder_contents_tool(
                ctx.deps.context.id_,
                folder_path,
                resolved_cursor,
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc

        return ListFolderContentsAgentResult.from_tool_result(
            result, self._store_cursor(result.next_cursor)
        )

    def search_by_filename(
        self,
        ctx: RunContext[AgentDeps],
        filename: str,
        search_string: str = "*",
        after_cursor: CursorHandle | None = None,
    ) -> SearchByFilenameAgentResult:
        """Search for files whose name contains the given substring.

        Returns matching files with their full paths and IDs. Use this when
        the user asks to find a file by name rather than by content.

        The name match can be narrowed with a Lucene query so that only files
        the query matches are searched by name, e.g. to find a filename within
        one file type or date range.

        Results are paginated, best matches first. The response includes
        has_more, next_cursor, total_count and count_relation.
        When has_more is True, call this tool again with the same filename
        and search_string and the returned next_cursor as after_cursor to
        retrieve the next page.
        Count_relation is set to "eq" if the total_count is exact.
        If it is set to "gte" the total_count is a lower bound.

        Args:
            filename: Substring to match against filenames (case-insensitive).
            search_string: Optional Elasticsearch Lucene query the files have
                to match as well, as returned by suggest_queries. Defaults to
                "*", which searches the whole index. Must be repeated
                unchanged when paging.
            after_cursor: Opaque pagination cursor from a previous call's
                next_cursor field. Cursors belong to the tool that produced
                them; do not pass one from a different tool. Omit for the
                first page.
        """
        resolved_cursor = self._resolve_cursor(after_cursor, "flat_files")
        try:
            result = self._task_call_service.call_search_by_filename_tool(
                ctx.deps.context.id_,
                filename,
                search_string,
                resolved_cursor,
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

        return SearchByFilenameAgentResult.from_tool_result(
            result, self._store_cursor(result.next_cursor)
        )

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

    def add_tags_to_file(
        self, ctx: RunContext[AgentDeps], file_id: str, tags: Tags
    ) -> AddTagsToFileResult:
        """Add one or more tags to a single file.

        The tags are added to whatever the file already carries; nothing is removed.
        Use this when the user asks you to tag or label a document. To tag every file
        a query matches, use the bulk metadata action instead.

        Args:
            file_id: UUID string of the file to tag.
            tags: Tag names to add to the file. At least one.
        """
        try:
            result = self._task_call_service.call_add_tags_to_file_tool(
                ctx.deps.context.id_, file_id, tags
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(ToolSource(file_id=UUID(result.file_id)))
        return result

    def update_file(
        self,
        ctx: RunContext[AgentDeps],
        file_id: str,
        request: UpdateFileRequest,
    ) -> UpdateFileResult:
        """Set the seen, flagged or hidden state of a single file.

        At least one flag has to be given; a flag left out of request keeps its
        current value. Use this when the user asks you to mark a file as seen or
        unseen, flag or unflag it, or hide or unhide it. To change every file a query
        matches, use the bulk metadata action instead.

        Args:
            file_id: UUID string of the file to update.
            request: The flags to set: seen marks the file as seen (True) or unseen
                (False), flagged flags (True) or unflags (False) it, and hidden hides
                (True) or unhides (False) it.
        """
        if request.sets_nothing:
            raise ModelRetry("Give at least one of seen, flagged or hidden to update.")
        try:
            result = self._task_call_service.call_update_file_tool(
                ctx.deps.context.id_, file_id, request
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        except LookupError as exc:
            raise ToolFailed(str(exc)) from exc
        ctx.deps.source_collector.append(ToolSource(file_id=UUID(result.file_id)))
        return result
