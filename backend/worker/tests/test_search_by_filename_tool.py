from typing import cast
from unittest.mock import MagicMock

import pytest
from common.ai_context.tool_models import SearchByFilenameResult
from common.dependencies import get_file_repository
from common.file.file_repository import FilePurePath, FlatFilesResult, TreePathsNode
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.models.es_repository import PointInTimeExpiredError
from common.services.query_builder import AI_PIT_KEEPALIVE, QueryBuilderException

from worker.ai.tasks.search_by_filename_tool import search_by_filename_work_task

OPENED_PIT = "pit-opened-by-the-tool"


def _make_node(path: str, file_id: str | None = "file-1") -> TreePathsNode:
    return TreePathsNode(full_path=FilePurePath(path), file_count=0, file_id=file_id)


def _set_result(
    *, nodes: list[TreePathsNode], next_cursor: SearchAfterCursor | None
) -> MagicMock:
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.open_point_in_time.return_value = OPENED_PIT
    file_repository.get_flat_files_by_query.return_value = FlatFilesResult(
        nodes=nodes, next_cursor=next_cursor
    )
    return file_repository


def _run(
    filename: str,
    after_cursor: SearchAfterCursor | None = None,
    search_string: str = "*",
) -> SearchByFilenameResult:
    result = search_by_filename_work_task(filename, search_string, after_cursor)
    assert isinstance(result, SearchByFilenameResult)
    return result


def test_pagination_ends_when_the_repository_hands_out_no_cursor():
    """The only case in which the tool reports the result set as exhausted."""
    _set_result(nodes=[_make_node("//s/report.pdf")], next_cursor=None)

    result = _run("report")

    assert result.has_more is False
    assert result.next_cursor is None


def test_entries_without_a_file_id_are_dropped_but_still_report_more():
    """A directory node carries no file_id.

    Dropping it must not be mistaken for the end of the result set — the repository
    cursor decides that.
    """
    _set_result(
        nodes=[_make_node("//s/report.pdf"), _make_node("//s/dir", file_id=None)],
        next_cursor=SearchAfterCursor(src="flat_files", last_sort=["//s/dir"]),
    )

    result = _run("report")

    assert [f.full_path for f in result.files] == ["//s/report.pdf"]
    assert result.has_more is True


def test_the_first_page_opens_a_point_in_time():
    """The search sorts on _score, which BM25 reads from index-wide statistics, so a
    page read against a different snapshot than the cursor was minted in resumes from a
    score that has since moved.

    The snapshot is what holds the sort keys still.
    """
    file_repository = _set_result(
        nodes=[_make_node("//s/report.pdf")], next_cursor=None
    )

    _run("report")

    file_repository.open_point_in_time.assert_called_once_with(
        keep_alive=AI_PIT_KEEPALIVE
    )
    query = file_repository.get_flat_files_by_query.call_args.kwargs["query"]
    assert query.query_id == OPENED_PIT
    # Not the ten-second default of QueryParameters, which a paging run outlives.
    assert query.keep_alive == AI_PIT_KEEPALIVE


def test_a_later_page_reuses_the_cursors_point_in_time():
    """Every page of one run has to read the same snapshot, so only the first opens
    one."""
    file_repository = _set_result(nodes=[], next_cursor=None)
    cursor = SearchAfterCursor(
        src="flat_files", last_sort=[1.0, "//s/report.pdf"], pit="pit-from-page-one"
    )

    _run("report", cursor)

    file_repository.open_point_in_time.assert_not_called()
    query = file_repository.get_flat_files_by_query.call_args.kwargs["query"]
    assert query.query_id == "pit-from-page-one"


def test_an_expired_point_in_time_is_reported_as_an_unusable_cursor():
    """The agent has no use for the distinction: either way the cursor cannot be
    resumed, and the answer is to start again without one."""
    file_repository = _set_result(nodes=[], next_cursor=None)
    file_repository.get_flat_files_by_query.side_effect = PointInTimeExpiredError()
    cursor = SearchAfterCursor(
        src="flat_files", last_sort=[1.0, "//s/report.pdf"], pit="a-lapsed-pit"
    )

    with pytest.raises(InvalidPaginationCursorError):
        _run("report", cursor)


def test_the_search_string_narrows_the_name_match():
    """The name wildcard runs over the hits of this query rather than the whole index,
    which is what lets the agent scope a filename search it would otherwise have to page
    through."""
    file_repository = _set_result(nodes=[], next_cursor=None)

    result = _run("report", search_string="file_type:pdf")

    query = file_repository.get_flat_files_by_query.call_args.kwargs["query"]
    assert query.search_string == "file_type:pdf"
    # Echoed back, because the cursor is bound to it and the next page has to repeat
    # it unchanged.
    assert result.search_string == "file_type:pdf"


def test_the_whole_index_is_searched_by_default():
    """Omitting the query matches the name against the whole index."""
    file_repository = _set_result(nodes=[], next_cursor=None)

    _run("report")

    query = file_repository.get_flat_files_by_query.call_args.kwargs["query"]
    assert query.search_string == "*"


def test_an_unparsable_search_string_comes_back_as_a_value_error():
    """search_string reaches the tool from the model, so a broken query is a mistake the
    agent can correct — not a backend failure."""
    file_repository = _set_result(nodes=[], next_cursor=None)
    file_repository.get_flat_files_by_query.side_effect = QueryBuilderException(
        "unexpected end of query"
    )

    with pytest.raises(ValueError, match="Invalid Lucene query"):
        _run("report", search_string="content:(")


def test_a_broken_query_on_a_resumed_page_is_reported_as_an_unusable_cursor():
    """ES answers a malformed point-in-time with the same error as a malformed query, so
    a page resumed from a cursor must not send the agent off to fix a query string that
    is fine."""
    file_repository = _set_result(nodes=[], next_cursor=None)
    file_repository.get_flat_files_by_query.side_effect = QueryBuilderException(
        "illegal_argument_exception"
    )
    cursor = SearchAfterCursor(
        src="flat_files", last_sort=[1.0, "//s/report.pdf"], pit="a-corrupted-pit"
    )

    with pytest.raises(InvalidPaginationCursorError):
        _run("report", cursor)
