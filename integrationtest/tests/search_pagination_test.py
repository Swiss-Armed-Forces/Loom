import pytest

from utils.fetch_from_api import (
    fetch_files_from_api,
    get_file_preview_by_file_id_without_waiting,
)
from utils.upload_asset import upload_asset

PAGINATION_TEST_FILE_COUNT = 11
ASSET_FILE_NAME = "empty_file.txt"


class TestPagination:
    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        for i in range(PAGINATION_TEST_FILE_COUNT):
            upload_asset(
                ASSET_FILE_NAME,
                f"{i}{ASSET_FILE_NAME}",
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
        assert len(files.files) == 9
        for f in files.files:
            file_ids.add(f.file_id)

        assert len(file_ids) == 11

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
            assert f"//api-upload/{i}{ASSET_FILE_NAME}" == file_paths[i]
