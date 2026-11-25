# pylint: disable=redefined-outer-name
"""Unit tests for ToolService error mapping using an injected test double."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from ag_ui.core import Tool as AGUITool
from common.ai_context.ai_context_repository import (
    AiContext,
    CapabilityId,
    ModeId,
)
from common.ai_context.tool_models import (
    AddTagsToFileResult,
    CursorHandle,
    ExecuteQueryResult,
    ExecuteQueryResultFile,
    FolderEntry,
    GetFileFieldResult,
    GetFileResult,
    ListFolderContentsResult,
    RagSearchResult,
    SearchByFilenameResult,
    SuggestQueriesResult,
    ToolSource,
    UpdateFileResult,
)
from common.dependencies import (
    get_file_repository,
    get_redis_cache_client,
    get_task_scheduling_service,
)
from common.models.cursor_pagination import CursorSource, SearchAfterCursor
from common.services.task_scheduling_service import UpdateFileRequest
from pydantic_ai import ModelRetry
from pydantic_ai.capabilities import Capability
from pydantic_ai.exceptions import ToolFailed
from redis import StrictRedis

from api.services.agent_deps import AgentDeps
from api.services.bulk_tool_service import BulkToolService
from api.services.task_call_service import TaskCallService
from api.services.tool_service import ToolService

_WRITING_CAPABILITIES = {CapabilityId.ENRICHMENT}


def _make_ctx(deps: AgentDeps) -> MagicMock:
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


def _seed_cursor(redis_cache_client_mock: MagicMock, src: CursorSource) -> str:
    """Store a cursor the way a previous page would have, and hand back both halves."""
    stored = SearchAfterCursor(src=src, last_sort=["//a"])

    redis_cache_client_mock.hget.return_value = stored.model_dump_json().encode("utf-8")

    return stored


def _make_agui_tool(
    name: str,
    description: str = "",
    capabilities: list[CapabilityId] | None = None,
) -> AGUITool:
    extra: dict[str, list[CapabilityId]] = (
        {"capabilities": capabilities} if capabilities else {}
    )
    return AGUITool(name=name, description=description, parameters={}, **extra)


@pytest.fixture
def task_call_service_mock() -> MagicMock:
    return MagicMock(spec=TaskCallService)


@pytest.fixture
def redis_cache_client_mock() -> MagicMock:
    return MagicMock(spec=StrictRedis)


@pytest.fixture
def tool_service(
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
) -> ToolService:
    return ToolService(
        task_call_service_mock,
        redis_cache_client_mock,
        BulkToolService(
            get_task_scheduling_service(),
            get_file_repository(),
            get_redis_cache_client(),
        ),
    )


@pytest.fixture
def deps() -> AgentDeps:
    return AgentDeps(context=AiContext())


# ---------------------------------------------------------------------------
# execute_query
# ---------------------------------------------------------------------------


def test_execute_query_success(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    file_id = uuid4()
    expected = ExecuteQueryResult(
        files=[ExecuteQueryResultFile(file_id=str(file_id), text="snippet", score=1.0)],
    )
    task_call_service_mock.call_execute_query_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.execute_query(ctx, "content:hello").return_value

    assert result.files == expected.files
    assert deps.source_collector == [ToolSource(file_id=file_id, text="snippet")]


def test_execute_query_value_error_raises_model_retry(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_execute_query_tool.side_effect = ValueError(
        "bad query syntax"
    )

    ctx = _make_ctx(deps)
    with pytest.raises(ModelRetry, match="bad query syntax"):
        tool_service.execute_query(ctx, "]invalid[")


# ---------------------------------------------------------------------------
# get_file
# ---------------------------------------------------------------------------


def test_get_file_success(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    file_id = uuid4()
    expected = GetFileResult(
        file_id=str(file_id),
        full_path="/docs/file.txt",
        available_fields=[],
    )
    task_call_service_mock.call_get_file_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.get_file(ctx, str(file_id)).return_value

    assert result is expected
    assert deps.source_collector == [ToolSource(file_id=file_id)]


def test_get_file_value_error_raises_model_retry(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_get_file_tool.side_effect = ValueError(
        "not a valid uuid"
    )

    ctx = _make_ctx(deps)
    with pytest.raises(ModelRetry, match="not a valid uuid"):
        tool_service.get_file(ctx, "not-a-uuid")


def test_get_file_lookup_error_raises_tool_failed(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_get_file_tool.side_effect = LookupError(
        "file not found"
    )

    ctx = _make_ctx(deps)
    with pytest.raises(ToolFailed, match="file not found"):
        tool_service.get_file(ctx, str(uuid4()))


# ---------------------------------------------------------------------------
# get_file_field
# ---------------------------------------------------------------------------


def test_get_file_field_success(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    file_id = uuid4()
    expected = GetFileFieldResult(
        file_id=str(file_id), field="content", value="full content"
    )
    task_call_service_mock.call_get_file_field_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.get_file_field(ctx, str(file_id), "content").return_value

    assert result is expected
    assert deps.source_collector == [ToolSource(file_id=file_id, text="full content")]


def test_get_file_field_value_error_raises_model_retry(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_get_file_field_tool.side_effect = ValueError(
        "unknown field 'bogus'"
    )

    ctx = _make_ctx(deps)
    with pytest.raises(ModelRetry, match="unknown field"):
        tool_service.get_file_field(ctx, str(uuid4()), "bogus")


def test_get_file_field_lookup_error_raises_tool_failed(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_get_file_field_tool.side_effect = LookupError(
        "field not available"
    )

    ctx = _make_ctx(deps)
    with pytest.raises(ToolFailed, match="field not available"):
        tool_service.get_file_field(ctx, str(uuid4()), "summary")


# ---------------------------------------------------------------------------
# list_folder_contents
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paginated", [False, True])
def test_list_folder_contents_dispatches_and_returns(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
    deps: AgentDeps,
    paginated: bool,
):

    expected = ListFolderContentsResult(
        folder_path="/",
        entries=[
            FolderEntry(full_path="//docs", is_file=False, file_count=5),
            FolderEntry(
                full_path="//readme.txt",
                is_file=True,
                file_count=1,
                file_id="abc",
            ),
        ],
    )
    task_call_service_mock.call_list_folder_contents_tool.return_value = expected

    ctx = _make_ctx(deps)
    seeded = (
        _seed_cursor(redis_cache_client_mock, "list_folder_contents")
        if paginated
        else None
    )
    result = tool_service.list_folder_contents(
        ctx, "/", after_cursor=seeded if seeded else None
    )

    assert result.entries == expected.entries
    assert result.folder_path == expected.folder_path
    # The handle is resolved before dispatch: the task gets the cursor itself.
    task_call_service_mock.call_list_folder_contents_tool.assert_called_once_with(
        deps.context.id_, "/", seeded if seeded else None
    )


# ---------------------------------------------------------------------------
# search_by_filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paginated", [False, True])
def test_search_by_filename_dispatches_and_returns(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
    deps: AgentDeps,
    paginated: bool,
):

    expected = SearchByFilenameResult(query="report", files=[])
    task_call_service_mock.call_search_by_filename_tool.return_value = expected

    ctx = _make_ctx(deps)
    seeded = _seed_cursor(redis_cache_client_mock, "flat_files") if paginated else None
    result = tool_service.search_by_filename(
        ctx, "report", after_cursor="Whatever" if seeded else None
    )

    assert result.query == expected.query
    assert result.files == expected.files
    # The handle is resolved before dispatch: the task gets the cursor itself.
    task_call_service_mock.call_search_by_filename_tool.assert_called_once_with(
        deps.context.id_, "report", "*", seeded if seeded else None
    )


def test_search_by_filename_passes_the_search_string(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The query narrows which files are name-matched, so it has to reach the task."""
    task_call_service_mock.call_search_by_filename_tool.return_value = (
        SearchByFilenameResult(query="report", search_string="file_type:pdf", files=[])
    )

    result = tool_service.search_by_filename(
        _make_ctx(deps), "report", search_string="file_type:pdf"
    )

    task_call_service_mock.call_search_by_filename_tool.assert_called_once_with(
        deps.context.id_, "report", "file_type:pdf", None
    )
    # Echoed back so the agent repeats it unchanged on the next page.
    assert result.search_string == "file_type:pdf"


def test_search_by_filename_reports_an_invalid_query_as_a_retry(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """A query the model composed is the model's to fix, so the failure has to come back
    as something it can act on rather than as a tool error."""
    task_call_service_mock.call_search_by_filename_tool.side_effect = ValueError(
        "Invalid Lucene query 'content:('"
    )

    with pytest.raises(ModelRetry):
        tool_service.search_by_filename(
            _make_ctx(deps), "report", search_string="content:("
        )


# ---------------------------------------------------------------------------
# rag_search
# ---------------------------------------------------------------------------


def test_rag_search_reads_the_whole_index_by_default(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The question is what the pipeline answers, never what it searches with."""
    task_call_service_mock.call_rag_search_tool.return_value = RagSearchResult(
        answer="", chunks=[]
    )

    tool_service.rag_search(_make_ctx(deps), "who signed the lease?")

    task_call_service_mock.call_rag_search_tool.assert_called_once_with(
        deps.context.id_, "who signed the lease?", "*"
    )


def test_rag_search_bounds_the_corpus_with_the_query(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """Both arguments are prose to a type checker, so the pair has to be pinned."""
    task_call_service_mock.call_rag_search_tool.return_value = RagSearchResult(
        answer="", chunks=[]
    )

    tool_service.rag_search(
        _make_ctx(deps), "who signed the lease?", query="file_type:pdf"
    )

    task_call_service_mock.call_rag_search_tool.assert_called_once_with(
        deps.context.id_, "who signed the lease?", "file_type:pdf"
    )


# ---------------------------------------------------------------------------
# suggest_queries with folder_path
# ---------------------------------------------------------------------------


def test_suggest_queries_passes_folder_path(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    expected = SuggestQueriesResult(candidates=[])
    task_call_service_mock.call_suggest_queries_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.suggest_queries(ctx, "invoices", folder_path="//emails")

    assert result is expected
    task_call_service_mock.call_suggest_queries_tool.assert_called_once_with(
        deps.context.id_, "invoices", "//emails"
    )


# ---------------------------------------------------------------------------
# execute_query with folder_path
# ---------------------------------------------------------------------------


def test_execute_query_passes_folder_path(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    expected = ExecuteQueryResult(files=[])
    task_call_service_mock.call_execute_query_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.execute_query(
        ctx, "content:hello", folder_path="//docs"
    ).return_value

    assert result.files == expected.files
    task_call_service_mock.call_execute_query_tool.assert_called_once_with(
        deps.context.id_, "content:hello", "//docs", None
    )


# ---------------------------------------------------------------------------
# capabilities property
# ---------------------------------------------------------------------------


def test_work_mode_exposes_deferred_capabilities(
    tool_service: ToolService,
):
    caps = tool_service.capabilities_for_mode(ModeId.WORK)
    assert _WRITING_CAPABILITIES <= {c.id for c in caps}
    assert all(c.defer_loading for c in caps)


def test_research_mode_cannot_write(
    tool_service: ToolService,
):
    """Research composes its own queries over the whole corpus with no user in the loop,
    so the capabilities that write are work-mode only."""
    cap_ids = {c.id for c in tool_service.capabilities_for_mode(ModeId.RESEARCH)}
    assert cap_ids.isdisjoint(_WRITING_CAPABILITIES)


def test_chat_mode_returns_no_capabilities(
    tool_service: ToolService,
):
    caps = tool_service.capabilities_for_mode(ModeId.CHAT)
    assert caps == []


def test_research_mode_includes_research_capability(
    tool_service: ToolService,
):
    caps = tool_service.capabilities_for_mode(ModeId.RESEARCH)
    cap_ids = {c.id for c in caps}
    assert CapabilityId.RESEARCH in cap_ids


def test_research_mode_shares_the_read_capability_with_work(
    tool_service: ToolService,
):
    caps = tool_service.capabilities_for_mode(ModeId.RESEARCH)
    assert {c.id for c in caps} == {
        CapabilityId.SEARCH_AND_BROWSE,
        CapabilityId.RESEARCH,
    }


def test_research_mode_defers_every_capability(
    tool_service: ToolService,
):
    """rag_search is no longer handed over up front: nothing is eager any more."""
    caps = tool_service.capabilities_for_mode(ModeId.RESEARCH)
    assert all(c.defer_loading for c in caps)


def test_search_and_browse_announces_its_ui_effect_in_work_mode_only(
    tool_service: ToolService,
):
    """The tools are the same in both modes; only the instructions differ, because that
    is the one field a per-mode capability can vary."""

    def read_capability(mode: ModeId) -> Capability[AgentDeps]:
        return next(
            c
            for c in tool_service.capabilities_for_mode(mode)
            if c.id == CapabilityId.SEARCH_AND_BROWSE
        )

    work = read_capability(ModeId.WORK)
    research = read_capability(ModeId.RESEARCH)

    work_instructions = "".join(work.get_instructions() or [])
    research_instructions = "".join(research.get_instructions() or [])

    assert "highlight" in work_instructions
    assert "highlight" not in research_instructions
    assert {t.name for t in work.tools} == {t.name for t in research.tools}


# ---------------------------------------------------------------------------
# route_frontend_tools
# ---------------------------------------------------------------------------


def test_route_frontend_tools_partitions_tools(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool("ask_user", "Ask a question"),
        _make_agui_tool("request_mode", "Request a mode"),
        _make_agui_tool(
            "get_highlighted_file",
            "Get the highlighted file",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
        _make_agui_tool(
            "discover_state",
            "Discover state",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
        _make_agui_tool(
            "read_state", "Read state", capabilities=[CapabilityId.UI_INTERACTION]
        ),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    always_on_names = {t.name for t in routed.always_on}
    assert always_on_names == {"ask_user", "request_mode"}


def test_route_frontend_tools_capability_ids(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool(
            "get_highlighted_file",
            "Get the highlighted file",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
        _make_agui_tool(
            "discover_state",
            "Discover state",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
    ]

    base_capabilities = tool_service.capabilities_for_mode(ModeId.WORK)
    routed = tool_service.route_frontend_tools(tools, base_capabilities)

    # Routing rebuilds the capabilities a frontend tool belongs to and passes the rest
    # through, so the mode's set comes out of it unchanged.
    assert {c.id for c in routed.capabilities} == {c.id for c in base_capabilities}


def test_route_frontend_tools_rebuilds_capabilities_with_frontend_tools(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool(
            "get_highlighted_file",
            "Get the highlighted file",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    ui_cap = next(c for c in routed.capabilities if c.id == CapabilityId.UI_INTERACTION)
    # The rebuilt capability should have toolsets (ExternalToolset with the frontend tool)
    assert len(ui_cap.toolsets) > 0


def test_route_frontend_tools_preserves_unaffected_capabilities(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool("ask_user", "Ask a question"),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    # No frontend tools mapped to any capability, so all should be original templates
    ui_cap = next(c for c in routed.capabilities if c.id == CapabilityId.UI_INTERACTION)
    # Without frontend tools to merge, the capability should have no external toolsets
    assert len(ui_cap.toolsets) == 0


def test_route_frontend_tools_unknown_tools_are_always_on(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool("unknown_tool", "Some tool"),
        _make_agui_tool("another_unknown", "Another"),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    always_on_names = {t.name for t in routed.always_on}
    assert always_on_names == {"unknown_tool", "another_unknown"}


# ---------------------------------------------------------------------------
# execute_query pagination handles
# ---------------------------------------------------------------------------

_REAL_CURSOR = SearchAfterCursor(
    src="execute_query", last_sort=[1.0, "abc"], pit="a-long-pit-id"
)


def test_execute_query_hands_out_a_handle_instead_of_the_cursor(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The cursor embeds a point-in-time id far too large to spend model context on
    twice per page, so the model only ever sees a short handle."""
    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[], has_more=True, next_cursor=_REAL_CURSOR
    )

    ctx = _make_ctx(deps)
    result = tool_service.execute_query(ctx, "content:hello").return_value

    assert result.next_cursor is not None
    assert "a-long-pit-id" not in result.next_cursor


def test_execute_query_resolves_a_handle_back_into_its_cursor(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
    deps: AgentDeps,
):

    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[]
    )

    redis_cache_client_mock.hget.return_value = _REAL_CURSOR.model_dump_json().encode(
        "utf-8"
    )

    ctx = _make_ctx(deps)
    tool_service.execute_query(
        ctx, "content:hello", after_cursor=CursorHandle("handle-1")
    )

    task_call_service_mock.call_execute_query_tool.assert_called_once_with(
        deps.context.id_, "content:hello", None, _REAL_CURSOR
    )


def test_execute_query_rejects_a_handle_from_another_run(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
    deps: AgentDeps,
):
    """Handles live only as long as the agent run, so a stale one has to be reported
    rather than dispatched as an opaque cursor."""
    redis_cache_client_mock.hget.return_value = None

    ctx = _make_ctx(deps)
    with pytest.raises(ModelRetry):
        tool_service.execute_query(
            ctx, "content:hello", after_cursor=CursorHandle("stale-handle")
        )

    task_call_service_mock.call_execute_query_tool.assert_not_called()


def test_execute_query_rejects_a_handle_minted_by_another_tool(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    redis_cache_client_mock: MagicMock,
    deps: AgentDeps,
):
    """A cursor only makes sense to the search that minted it, and the agent mixing two
    up is worth catching before it costs a task round-trip."""
    ctx = _make_ctx(deps)

    other_cursor = SearchAfterCursor(
        src="flat_files", last_sort=[1.0, "abc"], pit="a-long-pit-id"
    )
    redis_cache_client_mock.hget.return_value = other_cursor.model_dump_json().encode(
        "utf-8"
    )

    with pytest.raises(ModelRetry, match="different tool"):
        tool_service.execute_query(
            ctx, "content:hello", after_cursor=CursorHandle("handle-1")
        )

    task_call_service_mock.call_execute_query_tool.assert_not_called()


def test_execute_query_without_a_further_page_hands_out_no_handle(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[], has_more=False, next_cursor=None
    )

    ctx = _make_ctx(deps)
    result = tool_service.execute_query(ctx, "content:hello").return_value

    assert result.next_cursor is None


# ---------------------------------------------------------------------------
# file_curation
# ---------------------------------------------------------------------------


def test_add_tags_to_file_dispatches_and_cites_the_file(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    file_id = uuid4()
    task_call_service_mock.call_add_tags_to_file_tool.return_value = (
        AddTagsToFileResult(file_id=str(file_id), tags_added=["rhine-2024"])
    )

    result = tool_service.add_tags_to_file(
        _make_ctx(deps), str(file_id), ["rhine-2024"]
    )

    assert result.tags_added == ["rhine-2024"]
    task_call_service_mock.call_add_tags_to_file_tool.assert_called_once_with(
        deps.context.id_, str(file_id), ["rhine-2024"]
    )
    assert deps.source_collector == [ToolSource(file_id=file_id)]


def test_add_tags_to_file_reports_a_missing_file_as_a_tool_failure(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_add_tags_to_file_tool.side_effect = LookupError(
        "File not found"
    )

    with pytest.raises(ToolFailed, match="File not found"):
        tool_service.add_tags_to_file(_make_ctx(deps), str(uuid4()), ["a"])


def test_update_file_passes_only_the_flags_it_was_given(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """A flag left out keeps its current value, so it must not reach the write as
    False."""
    file_id = uuid4()
    task_call_service_mock.call_update_file_tool.return_value = UpdateFileResult(
        file_id=str(file_id), flagged=True
    )

    tool_service.update_file(
        _make_ctx(deps), str(file_id), UpdateFileRequest(flagged=True)
    )

    task_call_service_mock.call_update_file_tool.assert_called_once_with(
        deps.context.id_, str(file_id), UpdateFileRequest(flagged=True)
    )


def test_update_file_without_a_flag_writes_nothing(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    with pytest.raises(ModelRetry):
        tool_service.update_file(_make_ctx(deps), str(uuid4()), UpdateFileRequest())

    task_call_service_mock.call_update_file_tool.assert_not_called()
