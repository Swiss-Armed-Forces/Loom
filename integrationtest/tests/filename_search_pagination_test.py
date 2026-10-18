"""Paging a filename search against a real Elasticsearch.

The unit tests behind ``search_by_filename`` drive a ``MagicMock`` search, so they
cannot see what Elasticsearch accepts.  Two things about this search only exist in the
real engine: it sorts on ``_score`` before ``full_path.keyword``, and a point-in-time
makes Elasticsearch append its own tiebreaker to that sort — which is why the second
page sends a ``search_after`` tuple longer than the sort clause declares, and why this
search cannot ``collapse`` its results.
"""

from common.dependencies import get_file_repository
from common.services.query_builder import QueryParameters

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset

ASSET_FILE_NAME = "empty_file.txt"
FILENAME_NEEDLE = "pagingneedle"
FILE_COUNT = 3
PAGE_SIZE = 1


def _upload_matching_files() -> None:
    for index in range(FILE_COUNT):
        upload_asset(ASSET_FILE_NAME, f"{FILENAME_NEEDLE}-{index}.txt")
    fetch_files_from_api(search_string="*", expected_no_of_files=FILE_COUNT)


def test_filename_search_pages_against_a_point_in_time():
    """Every page of a run reads one snapshot, so the point-in-time rides the cursor.

    Elasticsearch rejects a multi-value ``search_after`` on a collapsed search, and
    attaching a point-in-time is what makes the tuple multi-value — so this is the
    combination that has to keep working.
    """
    _upload_matching_files()
    file_repository = get_file_repository()
    point_in_time = file_repository.open_point_in_time(keep_alive="5m")
    query = QueryParameters(query_id=point_in_time, search_string="*")

    page = file_repository.get_flat_files_by_query(
        query=query, filename=FILENAME_NEEDLE, page_size=PAGE_SIZE
    )
    seen = [str(node.full_path) for node in page.nodes]
    assert page.next_cursor is not None
    assert page.next_cursor.pit is not None

    # One iteration more than there can be pages: enough to reach the end, few enough
    # that a cursor which never advances fails here instead of looping.
    for _ in range(FILE_COUNT + 1):
        if page.next_cursor is None:
            break
        page = file_repository.get_flat_files_by_query(
            query=QueryParameters(query_id=point_in_time, search_string="*"),
            after=page.next_cursor,
            filename=FILENAME_NEEDLE,
            page_size=PAGE_SIZE,
        )
        seen.extend(str(node.full_path) for node in page.nodes)
    else:
        raise AssertionError("paging never reported the result set as exhausted")

    assert sorted(seen) == sorted(set(seen)), "a path was returned on two pages"
    assert len(seen) == FILE_COUNT
