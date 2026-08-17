from common.ai_context.tool_models import QuerySuggestion, SuggestQueriesResult

from worker.ai.tasks.suggest_queries_tool import suggest_queries_aggregate_task


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
