from typing import cast
from unittest.mock import MagicMock

import pytest
from common.ai_context.tool_models import ListFolderContentsResult
from common.dependencies import get_file_repository
from common.file.file_repository import FilePurePath, TreePathsNode, TreePathsResult
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.settings import settings

from worker.ai.tasks.list_folder_contents_tool import list_folder_contents_work_task

_FOLDER = "//source"
_DIGEST = SearchAfterCursor.digest(_FOLDER)


def _make_node(path: str, file_id: str | None = None) -> TreePathsNode:
    return TreePathsNode(full_path=FilePurePath(path), file_count=1, file_id=file_id)


def _set_result(
    *, nodes: list[TreePathsNode], next_page_cursor: str | None
) -> MagicMock:
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.get_full_paths_by_query.return_value = TreePathsResult(
        nodes=nodes, next_page_cursor=next_page_cursor
    )
    return file_repository


def _run(
    folder_path: str = _FOLDER, after_cursor: SearchAfterCursor | None = None
) -> ListFolderContentsResult:
    result = list_folder_contents_work_task(folder_path, after_cursor)
    assert isinstance(result, ListFolderContentsResult)
    return result


def test_the_repository_cursor_is_wrapped_into_an_opaque_cursor():
    """The repository paginates on a raw path.

    Handing that out directly would be indistinguishable from another tool's cursor, and
    would invite callers to interpret and compose it.
    """
    _set_result(nodes=[_make_node("//source/a")], next_page_cursor="//source/a")

    result = _run()

    assert result.has_more is True
    assert result.next_cursor is not None
    result.next_cursor.validate_for(
        expected_src="list_folder_contents",
        expected_digest=_DIGEST,
    )
    assert result.next_cursor.last_sort == ["//source/a"]


def test_no_repository_cursor_ends_pagination():
    _set_result(nodes=[_make_node("//source/a")], next_page_cursor=None)

    result = _run()

    assert result.has_more is False
    assert result.next_cursor is None


def test_a_cursor_is_unwrapped_before_it_reaches_the_repository():
    file_repository = _set_result(nodes=[], next_page_cursor=None)
    cursor = SearchAfterCursor(
        src="list_folder_contents", last_sort=["//source/a"], query_digest=_DIGEST
    )

    _run(after_cursor=cursor)

    assert file_repository.get_full_paths_by_query.call_args.kwargs["after"] == (
        "//source/a"
    )

    assert (
        file_repository.get_full_paths_by_query.call_args.kwargs["page_size"]
        == settings.tool.browse.page_size
    )


def test_entries_report_whether_they_are_files():
    _set_result(
        nodes=[_make_node("//source/dir"), _make_node("//source/f.txt", "file-1")],
        next_page_cursor=None,
    )

    result = _run()

    assert [e.is_file for e in result.entries] == [False, True]


@pytest.mark.parametrize(
    "cursor",
    [
        pytest.param(
            SearchAfterCursor(
                src="execute_query", last_sort=[1.0, "x"], query_digest=_DIGEST
            ),
            id="another-tools-cursor",
        ),
        pytest.param(
            SearchAfterCursor(
                src="list_folder_contents",
                last_sort=["//elsewhere"],
                query_digest=SearchAfterCursor.digest("//elsewhere"),
            ),
            id="another-folders-cursor",
        ),
    ],
)
def test_a_foreign_cursor_is_rejected(cursor: SearchAfterCursor):
    """Without validation a foreign cursor range-filters to nothing, and the model is
    told the folder is empty instead of being given an error."""
    _set_result(nodes=[], next_page_cursor=None)

    with pytest.raises(InvalidPaginationCursorError, match="Invalid pagination cursor"):
        _run(after_cursor=cursor)
