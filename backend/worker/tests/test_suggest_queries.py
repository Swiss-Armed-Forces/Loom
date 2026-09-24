from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import httpx
import pytest
from ai.llm_error_stubs import length_finish_reason_error
from common.ai_context.tool_models import QuerySuggestion, SuggestQueriesResult
from common.dependencies import get_file_repository, get_llm_suggest_queries_agent
from common.models.es_repository import QueryScoreStats
from openai import APIConnectionError, APITimeoutError, InternalServerError
from pydantic import ValidationError

from worker.ai.tasks.suggest_queries_tool import (
    _ElasticsearchQuery,
    suggest_queries_aggregate_task,
    suggest_queries_generate_task,
)

# pylint: disable=redefined-outer-name

QUERY_DESCRIPTION = "largest files by size"


def _tool_response(query_string: str) -> SimpleNamespace:
    """Build a minimal stand-in for an ``Agent.run_sync`` result."""
    return SimpleNamespace(output=_ElasticsearchQuery(query_string=query_string))


def _validation_error() -> ValidationError:
    """What a provider ignoring the strict JSON schema would surface as."""
    try:
        _ElasticsearchQuery.model_validate({"query_string": None})
    except ValidationError as e:
        return e
    raise AssertionError("expected _ElasticsearchQuery validation to fail")


@pytest.fixture
def suggest_queries_agent() -> MagicMock:
    """The suggest_queries LLM agent, mocked and pre-set with a successful response.

    ``mock_init`` (run by the autouse ``dependencies_init`` fixture) installs the global
    agent as a ``MagicMock``; we fetch it through the public
    ``get_llm_suggest_queries_agent`` accessor and configure it.
    """
    agent = cast(MagicMock, get_llm_suggest_queries_agent())
    agent.run_sync.return_value = _tool_response("size:>1000000")
    return agent


@pytest.fixture
def file_repository() -> MagicMock:
    """The file repository, mocked and pre-set with real (non-``MagicMock``) values.

    Both stand-ins have to be concrete: ``QueryParameters.query_id`` is a ``str | None``
    and ``QuerySuggestion.matching_docs`` an ``int``, so the default ``MagicMock``
    attributes fail validation and get swallowed by the counting ``except`` clause.
    """
    repository = cast(MagicMock, get_file_repository())
    repository.open_point_in_time.return_value = "test-pit-id"
    repository.count_and_score_stats_by_query.return_value = QueryScoreStats(
        total=42, max_score=3.5, avg_score=2.1
    )
    return repository


def test_aggregate_deduplicates_keeping_highest_count():
    candidates = [
        QuerySuggestion(
            query="foo", matching_docs=5, max_score=1.0, avg_score=0.8
        ).model_dump(),
        QuerySuggestion(
            query="foo", matching_docs=10, max_score=3.5, avg_score=2.1
        ).model_dump(),
        QuerySuggestion(
            query="bar", matching_docs=3, max_score=2.0, avg_score=1.5
        ).model_dump(),
    ]

    result = suggest_queries_aggregate_task(candidates)
    assert isinstance(result, SuggestQueriesResult)

    queries = {c.query: c for c in result.candidates}
    assert len(queries) == 2
    assert queries["foo"].matching_docs == 10
    assert queries["foo"].max_score == 3.5
    assert queries["foo"].avg_score == 2.1
    assert queries["bar"].matching_docs == 3
    assert queries["bar"].max_score == 2.0
    assert queries["bar"].avg_score == 1.5


def test_aggregate_filters_zero_matches():
    candidates = [
        QuerySuggestion(query="nope", matching_docs=0).model_dump(),
        QuerySuggestion(
            query="yes", matching_docs=1, max_score=0.5, avg_score=0.5
        ).model_dump(),
    ]

    result = suggest_queries_aggregate_task(candidates)
    assert isinstance(result, SuggestQueriesResult)

    assert len(result.candidates) == 1
    assert result.candidates[0].query == "yes"


def test_aggregate_sorts_by_matching_docs_descending():
    candidates = [
        QuerySuggestion(
            query="low", matching_docs=2, max_score=5.0, avg_score=4.0
        ).model_dump(),
        QuerySuggestion(
            query="high", matching_docs=20, max_score=1.0, avg_score=0.8
        ).model_dump(),
        QuerySuggestion(
            query="mid", matching_docs=10, max_score=3.0, avg_score=2.0
        ).model_dump(),
    ]

    result = suggest_queries_aggregate_task(candidates)
    assert isinstance(result, SuggestQueriesResult)

    assert [c.query for c in result.candidates] == ["high", "mid", "low"]


def test_aggregate_unwraps_nested_list():
    """Celery chord + self.replace() may wrap results in an extra list."""
    inner = [
        QuerySuggestion(
            query="q", matching_docs=5, max_score=2.0, avg_score=1.5
        ).model_dump(),
    ]

    result = suggest_queries_aggregate_task([inner])
    assert isinstance(result, SuggestQueriesResult)

    assert len(result.candidates) == 1
    assert result.candidates[0].max_score == 2.0
    assert result.candidates[0].avg_score == 1.5


# ---------------------------------------------------------------------------
# suggest_queries_generate_task -- candidate failures must not be fatal
# ---------------------------------------------------------------------------


def test_generate_returns_suggestion_on_success(
    suggest_queries_agent: MagicMock, file_repository: MagicMock
):
    result = suggest_queries_generate_task(QUERY_DESCRIPTION)

    assert result == QuerySuggestion(
        query="size:>1000000", matching_docs=42, max_score=3.5, avg_score=2.1
    )
    suggest_queries_agent.run_sync.assert_called_once()
    file_repository.count_and_score_stats_by_query.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(length_finish_reason_error(), id="length-limit-reached"),
        pytest.param(
            APIConnectionError(request=httpx.Request("POST", "http://tool-llm")),
            id="connection-error",
        ),
        pytest.param(
            APITimeoutError(request=httpx.Request("POST", "http://tool-llm")),
            id="timeout",
        ),
        pytest.param(
            InternalServerError(
                "upstream exploded",
                response=httpx.Response(
                    500, request=httpx.Request("POST", "http://tool-llm")
                ),
                body=None,
            ),
            id="server-error",
        ),
        pytest.param(_validation_error(), id="schema-violation"),
    ],
)
def test_generate_drops_candidate_when_llm_fails(
    suggest_queries_agent: MagicMock, error: Exception
):
    """A failing candidate must degrade, never raise.

    Regression test for #287: this task runs as a chord member, and a chord aborts as
    soon as any member raises -- discarding every sibling candidate that succeeded.
    """
    suggest_queries_agent.run_sync.side_effect = error

    result = suggest_queries_generate_task(QUERY_DESCRIPTION)

    assert result == QuerySuggestion(query="", matching_docs=0)


def test_generate_drops_candidate_without_querying_elasticsearch(
    suggest_queries_agent: MagicMock, file_repository: MagicMock
):
    """A dropped candidate has no query string, so it must not hit Elasticsearch."""
    suggest_queries_agent.run_sync.side_effect = length_finish_reason_error()

    suggest_queries_generate_task(QUERY_DESCRIPTION)

    file_repository.count_and_score_stats_by_query.assert_not_called()


def test_dropped_candidates_do_not_suppress_successful_siblings():
    """The #287 scenario end to end: 1 candidate fails, the other 2 must survive."""
    dropped = QuerySuggestion(query="", matching_docs=0).model_dump()
    good = [
        QuerySuggestion(
            query="size:>1000000", matching_docs=42, max_score=3.5, avg_score=2.1
        ).model_dump(),
        QuerySuggestion(
            query="extension:.pdf", matching_docs=7, max_score=1.0, avg_score=0.8
        ).model_dump(),
    ]

    result = suggest_queries_aggregate_task([dropped, *good])
    assert isinstance(result, SuggestQueriesResult)

    assert [c.query for c in result.candidates] == ["size:>1000000", "extension:.pdf"]


def test_aggregate_returns_empty_when_every_candidate_dropped():
    """All candidates failing yields no suggestions rather than an error.

    Documents current behaviour -- see the open question in #287 about whether a total
    LLM outage should be distinguishable from "no good queries found".
    """
    dropped = [QuerySuggestion(query="", matching_docs=0).model_dump()] * 3

    result = suggest_queries_aggregate_task(dropped)
    assert isinstance(result, SuggestQueriesResult)

    assert result.candidates == []
