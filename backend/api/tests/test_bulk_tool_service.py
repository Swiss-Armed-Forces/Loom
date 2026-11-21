# pylint: disable=redefined-outer-name
"""Unit tests for the query-scoped bulk tools and the approval they are held for."""

from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common.ai_context.ai_context_repository import AiContext
from common.ai_context.tool_models import BulkEnrichmentAction, BulkMetadataAction
from common.dependencies import (
    get_file_repository,
    get_redis_cache_client,
    get_task_scheduling_service,
)
from common.services.query_builder import (
    AI_PIT_KEEPALIVE,
    QueryBuilderException,
    QueryParameters,
)
from common.services.task_scheduling_service import UpdateFileRequest
from pydantic_ai import ModelRetry
from pydantic_ai.exceptions import ApprovalRequired, ToolFailed

from api.services.agent_deps import AgentDeps
from api.services.bulk_tool_service import BulkApproval, BulkToolService

_PIT = "pit-at-approval-time"


def _make_ctx(deps: AgentDeps, tool_call_id: str = "call-1") -> MagicMock:
    """A context for the leg that asks: nothing has been approved yet."""
    ctx = MagicMock()
    ctx.deps = deps
    ctx.tool_call_id = tool_call_id
    ctx.tool_call_approved = False
    return ctx


def _approved_ctx(deps: AgentDeps, tool_call_id: str = "call-1") -> MagicMock:
    """A context for the leg that dispatches, with the answer held for that call."""
    ctx = _make_ctx(deps, tool_call_id)
    ctx.tool_call_approved = True
    return ctx


def _approved_query_parameters(
    query_string: str = "content:rhine",
) -> QueryParameters:
    """The query a dispatch is expected to carry: the snapshot the count came from."""
    return QueryParameters(
        query_id=_PIT, keep_alive=AI_PIT_KEEPALIVE, search_string=query_string
    )


def _hold(approval: BulkApproval, deps: AgentDeps | None = None) -> BulkApproval:
    """Hold an approval the way an answered question leaves one.

    The store answers the next GETDEL with the record; ``deps`` is the other half, and
    stands for the client naming that id in the request it answered with. Leaving it out
    is an answer that names nothing.
    """
    cast(MagicMock, get_redis_cache_client()).getdel.return_value = (
        approval.model_dump_json()
    )
    if deps is not None:
        deps.approved_bulk_ids = frozenset({approval.approval_id})
    return approval


@pytest.fixture
def file_repository_mock() -> MagicMock:
    repository = cast(MagicMock, get_file_repository())
    repository.open_point_in_time.return_value = _PIT
    return repository


@pytest.fixture
def task_scheduling_service_mock() -> MagicMock:
    return cast(MagicMock, get_task_scheduling_service())


@pytest.fixture
def bulk_tool_service() -> BulkToolService:
    return BulkToolService(
        get_task_scheduling_service(),
        get_file_repository(),
        get_redis_cache_client(),
    )


@pytest.fixture
def deps() -> AgentDeps:
    return AgentDeps(context=AiContext())


def test_an_unapproved_action_asks_with_the_count_and_dispatches_nothing(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The approval is raised by the tool itself, so no ordering of agent calls can
    reach a dispatch without the user having seen what it covers."""
    file_repository_mock.count_by_query.return_value = 312

    with pytest.raises(ApprovalRequired) as excinfo:
        bulk_tool_service.bulk_add_tags(
            _make_ctx(deps), "content:rhine", ["rhine-2024"]
        )

    metadata = excinfo.value.metadata or {}
    assert metadata["action"] == BulkMetadataAction.ADD_TAGS
    assert metadata["query_string"] == "content:rhine"
    assert metadata["matched_files"] == 312
    # The count is taken against a snapshot, which is what the dispatch is pinned to.
    assert file_repository_mock.count_by_query.call_args.args[0].query_id == _PIT
    task_scheduling_service_mock.dispatch_add_tags_to_files.assert_not_called()


def test_each_call_gets_an_approval_of_its_own(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    deps: AgentDeps,
):
    """Two bulk calls in one model response are two decisions: each is held under the
    call it was raised from, so an answer to one cannot dispatch the other."""
    file_repository_mock.count_by_query.return_value = 5
    redis_mock = cast(MagicMock, get_redis_cache_client())

    for tool_call_id in ("call-1", "call-2"):
        with pytest.raises(ApprovalRequired):
            bulk_tool_service.bulk_summarize(
                _make_ctx(deps, tool_call_id), "content:rhine"
            )

    keys = {call.args[0] for call in redis_mock.set.call_args_list}
    assert len(keys) == 2
    assert all(str(deps.context.id_) in key for key in keys)
    approval_ids = {
        BulkApproval.model_validate_json(call.args[1]).approval_id
        for call in redis_mock.set.call_args_list
    }
    assert len(approval_ids) == 2


def test_an_approved_action_dispatches_the_snapshot_it_counted(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The user agreed to a number, so the sweep runs on the point-in-time that number
    was taken from rather than on the index as it is by then."""
    _hold(
        BulkApproval(
            approval_id=uuid4(),
            action=BulkMetadataAction.ADD_TAGS,
            query_string="content:rhine",
            query_id=_PIT,
            matched_files=7,
        ),
        deps,
    )

    result = bulk_tool_service.bulk_add_tags(
        _approved_ctx(deps), "content:rhine", ["rhine-2024"]
    )

    assert result.matched_files == 7
    task_scheduling_service_mock.dispatch_add_tags_to_files.assert_called_once_with(
        query=_approved_query_parameters(), tags=["rhine-2024"]
    )
    file_repository_mock.count_by_query.assert_not_called()


def test_bulk_translate_dispatches_with_the_source_language(
    bulk_tool_service: BulkToolService,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    _hold(
        BulkApproval(
            approval_id=uuid4(),
            action=BulkEnrichmentAction.TRANSLATE,
            query_string="content:rhine",
            query_id=_PIT,
            matched_files=4,
        ),
        deps,
    )

    bulk_tool_service.bulk_translate(_approved_ctx(deps), "content:rhine", "de")

    task_scheduling_service_mock.dispatch_translate_files.assert_called_once_with(
        query=_approved_query_parameters(), lang="de"
    )


def test_an_action_with_no_held_approval_dispatches_nothing(
    bulk_tool_service: BulkToolService,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The record is read with GETDEL, so an answer is spent by the dispatch it bought
    and a call arriving after it finds nothing to act on."""
    redis_mock = cast(MagicMock, get_redis_cache_client())
    redis_mock.getdel.return_value = None

    with pytest.raises(ModelRetry, match="no longer held"):
        bulk_tool_service.bulk_summarize(_approved_ctx(deps), "content:rhine")

    redis_mock.getdel.assert_called_once()
    task_scheduling_service_mock.dispatch_summarize_files.assert_not_called()


def test_an_answer_that_names_no_approval_dispatches_nothing(
    bulk_tool_service: BulkToolService,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """The answer has to name the approval it is answering, so an approved call is one
    the panel that was shown the question sent and not one that merely addresses the
    same tool call."""
    _hold(
        BulkApproval(
            approval_id=uuid4(),
            action=BulkEnrichmentAction.SUMMARIZE,
            query_string="content:rhine",
            query_id=_PIT,
            matched_files=7,
        )
    )

    with pytest.raises(ToolFailed, match="does not name the approval"):
        bulk_tool_service.bulk_summarize(_approved_ctx(deps), "content:rhine")

    task_scheduling_service_mock.dispatch_summarize_files.assert_not_called()


def test_an_approval_for_another_call_dispatches_nothing(
    bulk_tool_service: BulkToolService,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """An approved call may come back with edited arguments, so what was agreed to is
    checked against what is about to run."""
    _hold(
        BulkApproval(
            approval_id=uuid4(),
            action=BulkMetadataAction.ADD_TAGS,
            query_string="content:rhine",
            query_id=_PIT,
            matched_files=7,
        ),
        deps,
    )

    with pytest.raises(ToolFailed, match="not the one that was approved"):
        bulk_tool_service.bulk_add_tags(
            _approved_ctx(deps), "content:everything", ["rhine-2024"]
        )

    task_scheduling_service_mock.dispatch_add_tags_to_files.assert_not_called()


def test_a_query_matching_nothing_is_not_put_to_the_user(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    deps: AgentDeps,
):
    file_repository_mock.count_by_query.return_value = 0

    with pytest.raises(ModelRetry, match="nothing to act on"):
        bulk_tool_service.bulk_summarize(_make_ctx(deps), "content:rhine")


def test_an_invalid_query_comes_back_as_a_retry(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """A query the model composed is the model's to fix, so Elasticsearch rejecting it
    must not kill the run."""
    file_repository_mock.count_by_query.side_effect = QueryBuilderException(
        "unexpected end of query"
    )

    with pytest.raises(ModelRetry, match="Invalid Lucene query"):
        bulk_tool_service.bulk_summarize(_make_ctx(deps), "content:(")

    task_scheduling_service_mock.dispatch_summarize_files.assert_not_called()


def test_an_empty_query_string_comes_back_as_a_retry(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    deps: AgentDeps,
):
    """QueryParameters refuses an empty search string, which reaches the agent the same
    way a malformed one does — and costs no snapshot."""
    with pytest.raises(ModelRetry, match="Invalid Lucene query"):
        bulk_tool_service.bulk_summarize(_make_ctx(deps), "")

    file_repository_mock.open_point_in_time.assert_not_called()


def test_bulk_update_files_without_a_flag_asks_for_nothing(
    bulk_tool_service: BulkToolService,
    file_repository_mock: MagicMock,
    task_scheduling_service_mock: MagicMock,
    deps: AgentDeps,
):
    """An approval for a write that sets nothing is a question not worth asking."""
    with pytest.raises(ModelRetry, match="at least one of seen"):
        bulk_tool_service.bulk_update_files(
            _make_ctx(deps), "content:rhine", UpdateFileRequest()
        )

    file_repository_mock.count_by_query.assert_not_called()
    task_scheduling_service_mock.dispatch_update.assert_not_called()
