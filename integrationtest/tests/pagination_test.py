from math import ceil
from uuid import uuid4

import pytest
from common.dependencies import get_celery_app
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from worker.ai.tasks.execute_query_tool import execute_query_tool_task
from worker.settings import settings

from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_preview_by_file_id_without_waiting,
)
from utils.upload_asset import upload_asset

# Tests assume that page_size > 6
PAGINATION_TEST_FILE_COUNT = settings.tool.execute_query.page_size + 1
ASSET_FILE_NAME = "empty_file.txt"
GET_TIMEOUT = 120


class TestPagination:
    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def setup_testfiles(cls):
        for i in range(PAGINATION_TEST_FILE_COUNT):
            upload_asset(
                ASSET_FILE_NAME,
                f"{ASSET_FILE_NAME}-{i}",
            )

        # wait for assets to be processes
        search_string = "*"
        file_count = PAGINATION_TEST_FILE_COUNT
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_fetch_first_page(self):
        page_size = 2
        search_string = "*"

        files = fetch_files_from_api(
            search_string=search_string,
            page_size=page_size,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )
        assert len(files.files) == 2

    def test_fetch_second_page(self):
        search_string = "*"

        file_ids = set()
        files = fetch_files_from_api(
            search_string=search_string,
            page_size=2,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )
        assert len(files.files) == 2
        for f in files.files:
            file_ids.add(f.file_id)

        files = fetch_files_from_api(
            search_string=search_string,
            sort_id=files.files[1].sort_id,
            page_size=9,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )
        assert len(files.files) == PAGINATION_TEST_FILE_COUNT - 2
        for f in files.files:
            file_ids.add(f.file_id)

        assert len(file_ids) == PAGINATION_TEST_FILE_COUNT

    def test_fetch_all_files(self):
        search_string = "*"
        fetch_files_from_api(
            search_string=search_string,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )

    def test_pagination_with_sorting(self):
        search_string = "*"
        files = fetch_files_from_api(
            search_string=search_string,
            sort_by_field="uploaded_datetime",
            sort_direction="asc",
            page_size=3,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )
        assert len(files.files) == 3

        file_paths = []
        for f in files.files:
            file_paths.append(
                get_file_preview_by_file_id_without_waiting(file_id=f.file_id).path
            )

        files = fetch_files_from_api(
            search_string=search_string,
            sort_by_field="uploaded_datetime",
            sort_direction="asc",
            page_size=3,
            sort_id=files.files[2].sort_id,
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
        )
        assert len(files.files) == 3

        for f in files.files:
            file_paths.append(
                get_file_preview_by_file_id_without_waiting(file_id=f.file_id).path
            )

        for i in range(6):
            assert f"//api-upload/{ASSET_FILE_NAME}-{i}" == file_paths[i]

    def test_execute_query_rejects_a_cursor_it_did_not_produce(self):
        foreign_cursor = SearchAfterCursor(
            src="list_folder_contents",
            last_sort=["//source"],
            query_digest=SearchAfterCursor.digest("//source"),
        )

        try:
            get_celery_app().send_task(
                execute_query_tool_task.name,
                args=["*", uuid4(), None, foreign_cursor],
            ).get(timeout=GET_TIMEOUT)
        except InvalidPaginationCursorError:
            return

        raise AssertionError(
            "InvalidPaginationCursorError exception should have been raised"
        )

    def test_execute_query_rejects_a_cursor_with_an_unusable_point_in_time(self):
        # Belongs to this tool and to this query, so it gets past validate_for and
        # reaches Elasticsearch, which rejects the point-in-time id. ES reports that
        # with the same illegal_argument_exception as a malformed Lucene query, and
        # only a live cluster tells the two apart.
        corrupt_pit_cursor = SearchAfterCursor(
            src="execute_query",
            last_sort=[1.0],
            pit="not-a-point-in-time",
            query_digest=SearchAfterCursor.digest("*"),
        )

        try:
            get_celery_app().send_task(
                execute_query_tool_task.name,
                args=["*", uuid4(), None, corrupt_pit_cursor],
            ).get(timeout=GET_TIMEOUT)
        except InvalidPaginationCursorError:
            return

        raise AssertionError(
            "InvalidPaginationCursorError exception should have been raised"
        )

    def test_execute_query_pagination_terminates_without_repeating_files(self):
        """Page through a corpus that does not fit on one page."""
        fetch_files_from_api(
            search_string="*",
            expected_no_of_files=PAGINATION_TEST_FILE_COUNT,
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE,
        )

        data = (
            get_celery_app()
            .send_task(
                execute_query_tool_task.name,
                args=["*", uuid4(), None, None],
            )
            .get(timeout=GET_TIMEOUT)
        )

        assert data.total_count == PAGINATION_TEST_FILE_COUNT
        page_length = len(data.files)
        # Without this the test would pass while never following a single cursor.
        assert 0 < page_length < PAGINATION_TEST_FILE_COUNT
        assert data.has_more is True

        seen = [f.file_id for f in data.files]
        # One iteration more than there can be pages: enough to reach the end, few
        # enough that a cursor which never terminates fails instead of looping.
        for _ in range(ceil(PAGINATION_TEST_FILE_COUNT / page_length) + 1):
            if not data.has_more:
                break
            assert data.next_cursor, "has_more without a cursor to follow"
            data = (
                get_celery_app()
                .send_task(
                    execute_query_tool_task.name,
                    args=["*", uuid4(), None, data.next_cursor],
                )
                .get(timeout=GET_TIMEOUT)
            )
            seen.extend(f.file_id for f in data.files)
        else:
            pytest.fail("execute-query kept reporting has_more and never finished")

        assert sorted(seen) == sorted(set(seen)), "a file was returned on two pages"
        assert len(seen) == PAGINATION_TEST_FILE_COUNT
