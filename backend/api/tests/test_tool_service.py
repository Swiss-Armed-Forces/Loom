# pylint: disable=redefined-outer-name
"""Unit tests for ToolService error mapping using an injected test double."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common.ai_context.ai_context_repository import AiContext
from common.ai_context.tool_models import (
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
from pydantic_ai import ModelRetry
from pydantic_ai.exceptions import ToolFailed

from api.services.task_call_service import TaskCallService
from api.services.tool_service import AgentDeps, ToolService


def _make_ctx(deps: AgentDeps) -> MagicMock:
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


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

    assert result is expected
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


def test_list_folder_contents_dispatches_and_returns(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
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
    result = tool_service.list_folder_contents(ctx, "/")

    assert result is expected
    task_call_service_mock.call_list_folder_contents_tool.assert_called_once_with(
        deps.context.id_, "/"
    )


# ---------------------------------------------------------------------------
# search_by_filename
# ---------------------------------------------------------------------------


def test_search_by_filename_dispatches_and_returns(
    tool_service: ToolService,
    task_call_service_mock: MagicMock,
    deps: AgentDeps,
):
    expected = SearchByFilenameResult(query="report", files=[])
    task_call_service_mock.call_search_by_filename_tool.return_value = expected

    ctx = _make_ctx(deps)
    result = tool_service.search_by_filename(ctx, "report")

    assert result is expected
    task_call_service_mock.call_search_by_filename_tool.assert_called_once_with(
        deps.context.id_, "report"
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

    assert result is expected
    task_call_service_mock.call_execute_query_tool.assert_called_once_with(
        deps.context.id_, "content:hello", "//docs"
    )
