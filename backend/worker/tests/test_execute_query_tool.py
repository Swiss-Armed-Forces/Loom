from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from common.ai_context.tool_models import ExecuteQueryResult
from common.dependencies import get_file_repository
from common.file.file_repository import File, FilePurePath
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.models.es_repository import (
    PagedSearchResult,
)
from elastic_transport import ApiResponseMeta
from elasticsearch import BadRequestError

from worker.ai.tasks.execute_query_tool import execute_query_work_task
from worker.settings import settings

_PAGE_SIZE = settings.tool.execute_query.page_size


def _bad_request_error() -> BadRequestError:
    """The error ES raises for an illegal_argument_exception, whatever caused it."""
    return BadRequestError(
        "illegal_argument_exception",
        cast(ApiResponseMeta, MagicMock(status=400)),
        None,
    )


def _make_file(name: str = "report.pdf") -> File:
    return File(
        full_name=FilePurePath(name),
        source="test",
        sha256="abc123",
        size=42,
    )


_QUERY = "content:hello"
_DIGEST = SearchAfterCursor.digest(_QUERY)


def _make_cursor(
    *,
    last_sort: list[object] | None = None,
    pit: str | None = "pit-1",
    digest: str | None = _DIGEST,
) -> SearchAfterCursor:
    return SearchAfterCursor(
        src="execute_query",
        last_sort=last_sort if last_sort is not None else [1.0, "w"],
        pit=pit,
        query_digest=digest,
    )


def _set_page(
    *,
    objs: list[File],
    total_hits: int,
    next_sort_id: list[object] | None,
    has_more: bool = False,
) -> MagicMock:
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.open_point_in_time.return_value = "pit-1"
    file_repository.get_page_by_query.return_value = PagedSearchResult[File](
        objs=objs,
        total_hits=total_hits,
        has_more=has_more,
        next_sort_id=next_sort_id,
    )
    return file_repository


def _run(
    query_string: str,
    after_cursor: SearchAfterCursor | None = None,
    folder_path: str | None = None,
) -> ExecuteQueryResult:
    result = execute_query_work_task(query_string, folder_path, after_cursor)
    assert isinstance(result, ExecuteQueryResult)
    return result


def test_full_page_reports_more_and_hands_out_a_cursor():
    _set_page(
        objs=[_make_file() for _ in range(_PAGE_SIZE)],
        total_hits=25,
        next_sort_id=[1.0, "sort-key"],
        has_more=True,
    )

    result = _run(_QUERY)

    assert result.total_count == 25
    assert result.has_more is True
    assert result.next_cursor is not None
    cursor = result.next_cursor
    cursor.validate_for(expected_src="execute_query", expected_digest=_DIGEST)
    assert cursor.last_sort == [1.0, "sort-key"]
    assert cursor.pit == "pit-1"


def test_last_page_reports_no_more():
    """The repository's lookahead found no further hit, so paging ends here even though
    the page is full."""
    _set_page(
        objs=[_make_file() for _ in range(_PAGE_SIZE)],
        total_hits=_PAGE_SIZE,
        next_sort_id=[0.5, "x"],
        has_more=False,
    )

    result = _run(_QUERY, after_cursor=_make_cursor())

    assert result.has_more is False
    assert result.next_cursor is None


def test_empty_page_does_not_emit_a_reset_cursor():
    """An empty page must not hand out a cursor that restarts at page one."""
    _set_page(objs=[], total_hits=25, next_sort_id=None)

    result = _run(_QUERY, after_cursor=_make_cursor())

    assert result.has_more is False
    assert result.next_cursor is None


def test_first_page_opens_a_point_in_time_and_follow_up_pages_reuse_it():
    file_repository = _set_page(
        objs=[_make_file() for _ in range(_PAGE_SIZE)],
        total_hits=25,
        next_sort_id=[1.0, "sort-key"],
        has_more=True,
    )

    first = _run(_QUERY)
    assert file_repository.open_point_in_time.call_count == 1

    assert first.next_cursor is not None
    _run(_QUERY, after_cursor=first.next_cursor)

    # No second snapshot: paging must stay on the snapshot of the first page.
    assert file_repository.open_point_in_time.call_count == 1
    query = file_repository.get_page_by_query.call_args.kwargs["query"]
    assert query.query_id == "pit-1"


def test_a_reopened_point_in_time_is_handed_on_instead_of_the_dead_one():
    """The repository reopens an expired point-in-time and writes the new id onto the
    query, so the cursor has to be minted from the query rather than from the cursor it
    was resumed from."""
    file_repository = _set_page(
        objs=[_make_file()],
        total_hits=25,
        next_sort_id=[1.0, "sort-key"],
        has_more=True,
    )

    def reopen(**kwargs: Any) -> PagedSearchResult[File]:
        kwargs["query"].query_id = "pit-2"
        return cast(
            PagedSearchResult[File], file_repository.get_page_by_query.return_value
        )

    file_repository.get_page_by_query.side_effect = reopen

    result = _run(_QUERY, after_cursor=_make_cursor(pit="pit-1"))

    assert result.next_cursor is not None
    cursor = result.next_cursor
    cursor.validate_for(expected_src="execute_query", expected_digest=_DIGEST)
    assert cursor.pit == "pit-2"


def test_results_are_sorted_by_descending_relevance():
    file_repository = _set_page(objs=[], total_hits=0, next_sort_id=None)

    _run(_QUERY)

    sort_params = file_repository.get_page_by_query.call_args.kwargs["sort_params"]
    assert sort_params.sort_by_field == "_score"
    assert sort_params.sort_direction == "desc"


def test_only_the_fields_the_file_requires_are_fetched():
    """A page ships one _source per hit, so fetching content — capped at 2 MiB per
    document — just to cut it down to a snippet would dominate the response."""
    file_repository = _set_page(objs=[], total_hits=0, next_sort_id=None)

    _run(_QUERY)

    call_kwargs = file_repository.get_page_by_query.call_args.kwargs
    assert "content" not in call_kwargs["source_includes"]
    assert "embeddings" not in call_kwargs["source_includes"]
    # The snippet comes from a highlight that falls back to the start of content.
    assert call_kwargs["leading_snippet_highlight"].field == "content"


def test_cursor_is_forwarded_as_the_search_after_sort_id():
    file_repository = _set_page(objs=[], total_hits=0, next_sort_id=None)

    _run(_QUERY, after_cursor=_make_cursor(last_sort=[1.0, "w"]))

    pagination = file_repository.get_page_by_query.call_args.kwargs["pagination_params"]
    assert pagination.sort_id == [1.0, "w"]
    assert pagination.page_size == _PAGE_SIZE


def test_a_cursor_for_another_query_is_rejected():
    _set_page(objs=[], total_hits=0, next_sort_id=None)
    cursor = _make_cursor(digest=SearchAfterCursor.digest("content:something-else"))

    with pytest.raises(InvalidPaginationCursorError, match="Invalid pagination cursor"):
        _run(_QUERY, after_cursor=cursor)


def test_a_cursor_for_another_folder_path_is_rejected():
    """folder_path is folded into the search string, so paging without repeating it
    would otherwise silently resume against an unfiltered query."""
    _set_page(
        objs=[_make_file()],
        total_hits=25,
        next_sort_id=[1.0, "sort-key"],
        has_more=True,
    )

    scoped = _run(_QUERY, folder_path="//docs")
    assert scoped.next_cursor is not None

    with pytest.raises(InvalidPaginationCursorError, match="Invalid pagination cursor"):
        _run(_QUERY, after_cursor=scoped.next_cursor)


def test_a_rejected_query_tells_the_caller_to_build_a_new_one():
    file_repository = _set_page(objs=[], total_hits=0, next_sort_id=None)
    file_repository.get_page_by_query.side_effect = _bad_request_error()

    with pytest.raises(ValueError, match="suggest_queries") as exc_info:
        _run(_QUERY)

    assert not isinstance(exc_info.value, InvalidPaginationCursorError)


def test_a_rejected_point_in_time_is_not_blamed_on_the_query():
    """ES rejects a malformed point-in-time id with the same error as a malformed query,
    and telling the model to rebuild a valid query gets paging nowhere."""
    file_repository = _set_page(objs=[], total_hits=0, next_sort_id=None)
    file_repository.get_page_by_query.side_effect = _bad_request_error()

    with pytest.raises(InvalidPaginationCursorError):
        _run(_QUERY, after_cursor=_make_cursor(pit="corrupted-pit"))


def test_another_tools_cursor_gives_an_actionable_error():
    """The task takes the cursor itself, so a corrupt payload is not reachable here —
    but a cursor minted by a different tool is, and resuming an unrelated sort would
    return a plausible but wrong page."""
    _set_page(objs=[], total_hits=0, next_sort_id=None)
    cursor = SearchAfterCursor(
        src="list_folder_contents", last_sort=["//docs"], query_digest=_DIGEST
    )

    with pytest.raises(InvalidPaginationCursorError, match="Invalid pagination cursor"):
        _run(_QUERY, after_cursor=cursor)
