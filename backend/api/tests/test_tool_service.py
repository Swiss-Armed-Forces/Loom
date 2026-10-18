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
    CursorHandle,
    ExecuteQueryResult,
    ExecuteQueryResultFile,
    FolderEntry,
    GetFileFieldResult,
    GetFileResult,
    ListFolderContentsResult,
    SearchByFilenameResult,
    SuggestQueriesResult,
    ToolSource,
)
from common.models.cursor_pagination import CursorSource, SearchAfterCursor
from pydantic_ai import ModelRetry
from pydantic_ai.exceptions import ToolFailed

from api.services.task_call_service import TaskCallService
from api.services.tool_service import (
    _MAX_TRACKED_CURSORS,
    AgentDeps,
    StoredCursor,
    ToolService,
)


def _make_ctx(deps: AgentDeps) -> MagicMock:
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


def _seed_cursor(deps: AgentDeps, src: CursorSource) -> StoredCursor:
    """Store a cursor the way a previous page would have, and hand back both halves."""
    stored = StoredCursor(
        handle=CursorHandle(f"handle-{len(deps.cursors)}"),
        cursor=SearchAfterCursor(src=src, last_sort=["//a"]),
    )
    deps.cursors.append(stored)
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
def tool_service(task_call_service_mock: MagicMock) -> ToolService:
    return ToolService(task_call_service_mock)


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
    result = tool_service.execute_query(ctx, "content:hello")

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
    result = tool_service.get_file(ctx, str(file_id))

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
    result = tool_service.get_file_field(ctx, str(file_id), "content")

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
    seeded = _seed_cursor(deps, "list_folder_contents") if paginated else None
    result = tool_service.list_folder_contents(
        ctx, "/", after_cursor=seeded.handle if seeded else None
    )

    assert result.entries == expected.entries
    assert result.folder_path == expected.folder_path
    # The handle is resolved before dispatch: the task gets the cursor itself.
    task_call_service_mock.call_list_folder_contents_tool.assert_called_once_with(
        deps.context.id_, "/", seeded.cursor if seeded else None
    )


# ---------------------------------------------------------------------------
# search_by_filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paginated", [False, True])
def test_search_by_filename_dispatches_and_returns(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
    paginated: bool,
):

    expected = SearchByFilenameResult(query="report", files=[])
    task_call_service_mock.call_search_by_filename_tool.return_value = expected

    ctx = _make_ctx(deps)
    seeded = _seed_cursor(deps, "flat_files") if paginated else None
    result = tool_service.search_by_filename(
        ctx, "report", after_cursor=seeded.handle if seeded else None
    )

    assert result.query == expected.query
    assert result.files == expected.files
    # The handle is resolved before dispatch: the task gets the cursor itself.
    task_call_service_mock.call_search_by_filename_tool.assert_called_once_with(
        deps.context.id_, "report", "*", seeded.cursor if seeded else None
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
    result = tool_service.execute_query(ctx, "content:hello", folder_path="//docs")

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
    assert len(caps) == 4
    ui_cap = caps[3]
    assert ui_cap.id == CapabilityId.UI_INTERACTION
    assert ui_cap.defer_loading is True


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


def test_research_mode_also_includes_work_capabilities(
    tool_service: ToolService,
):
    caps = tool_service.capabilities_for_mode(ModeId.RESEARCH)
    assert len(caps) == 4
    cap_ids = {c.id for c in caps}
    assert {
        CapabilityId.SEARCH_AND_BROWSE,
        CapabilityId.FILE_ACCESS,
        CapabilityId.AI_PROCESSING,
        CapabilityId.RESEARCH,
    } == cap_ids


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
            "set_search_query",
            "Set search query",
            capabilities=[CapabilityId.SEARCH_AND_BROWSE],
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
            "set_search_query",
            "Set search query",
            capabilities=[CapabilityId.SEARCH_AND_BROWSE],
        ),
        _make_agui_tool(
            "discover_state",
            "Discover state",
            capabilities=[CapabilityId.UI_INTERACTION],
        ),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    cap_ids = {c.id for c in routed.capabilities}
    assert cap_ids == {
        CapabilityId.SEARCH_AND_BROWSE,
        CapabilityId.FILE_ACCESS,
        CapabilityId.AI_PROCESSING,
        CapabilityId.UI_INTERACTION,
    }


def test_route_frontend_tools_rebuilds_capabilities_with_frontend_tools(
    tool_service: ToolService,
):
    tools = [
        _make_agui_tool(
            "set_search_query",
            "Set search query",
            capabilities=[CapabilityId.SEARCH_AND_BROWSE],
        ),
    ]

    routed = tool_service.route_frontend_tools(
        tools, tool_service.capabilities_for_mode(ModeId.WORK)
    )

    search_cap = next(
        c for c in routed.capabilities if c.id == CapabilityId.SEARCH_AND_BROWSE
    )
    # The rebuilt capability should have toolsets (ExternalToolset with the frontend tool)
    assert len(search_cap.toolsets) > 0


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
    search_cap = next(
        c for c in routed.capabilities if c.id == CapabilityId.SEARCH_AND_BROWSE
    )
    # Without frontend tools to merge, the capability should have no external toolsets
    assert len(search_cap.toolsets) == 0


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
    result = tool_service.execute_query(ctx, "content:hello")

    assert result.next_cursor is not None
    assert "a-long-pit-id" not in result.next_cursor
    assert deps.cursors[-1].cursor == _REAL_CURSOR


def test_execute_query_resolves_a_handle_back_into_its_cursor(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):

    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[]
    )

    ctx = _make_ctx(deps)
    deps.cursors.append(
        StoredCursor(handle=CursorHandle("handle-1"), cursor=_REAL_CURSOR)
    )
    tool_service.execute_query(
        ctx, "content:hello", after_cursor=CursorHandle("handle-1")
    )

    task_call_service_mock.call_execute_query_tool.assert_called_once_with(
        deps.context.id_, "content:hello", None, _REAL_CURSOR
    )


def test_execute_query_rejects_a_handle_from_another_run(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """Handles live only as long as the agent run, so a stale one has to be reported
    rather than dispatched as an opaque cursor."""
    ctx = _make_ctx(deps)
    with pytest.raises(ModelRetry):
        tool_service.execute_query(
            ctx, "content:hello", after_cursor=CursorHandle("stale-handle")
        )

    task_call_service_mock.call_execute_query_tool.assert_not_called()


def test_execute_query_rejects_a_handle_minted_by_another_tool(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """A cursor only makes sense to the search that minted it, and the agent mixing two
    up is worth catching before it costs a task round-trip."""
    ctx = _make_ctx(deps)
    seeded = _seed_cursor(deps, "list_folder_contents")

    with pytest.raises(ModelRetry, match="different tool"):
        tool_service.execute_query(ctx, "content:hello", after_cursor=seeded.handle)

    task_call_service_mock.call_execute_query_tool.assert_not_called()


def test_only_the_most_recent_handles_stay_resolvable(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The store is bounded rather than swept on a clock.

    The agent pages forward, so the oldest handle is the one that may fall off.
    """
    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[], has_more=True, next_cursor=_REAL_CURSOR
    )

    ctx = _make_ctx(deps)
    handles = [
        tool_service.execute_query(ctx, "content:hello").next_cursor
        for _ in range(_MAX_TRACKED_CURSORS + 1)
    ]
    assert len(deps.cursors) == _MAX_TRACKED_CURSORS

    with pytest.raises(ModelRetry):
        tool_service.execute_query(ctx, "content:hello", after_cursor=handles[0])

    newest = handles[-1]
    assert newest is not None
    tool_service.execute_query(ctx, "content:hello", after_cursor=newest)


def test_execute_query_without_a_further_page_hands_out_no_handle(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    task_call_service_mock.call_execute_query_tool.return_value = ExecuteQueryResult(
        files=[], has_more=False, next_cursor=None
    )

    ctx = _make_ctx(deps)
    result = tool_service.execute_query(ctx, "content:hello")

    assert result.next_cursor is None
    assert not deps.cursors
