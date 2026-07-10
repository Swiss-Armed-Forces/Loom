from pathlib import Path

import pytest
import requests
from api.routers.files import (
    GetFilesTreeQuery,
    GetFilesTreeResponse,
    GetFilesTreeSpineQuery,
)
from common.file.file_repository import (
    TREE_PATH_MAX_ELEMENT_COUNT,
)
from requests import HTTPError

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    build_search_string,
    fetch_files_from_api,
    fetch_query_id,
)
from utils.upload_asset import upload_asset, upload_bytes_asset

FILE_COUNT_TOP_LEVEL = 3
FILE_COUNT_BELOW_FRONTEND_LIMIT = TREE_PATH_MAX_ELEMENT_COUNT
FILE_COUNT_BELOW_BACKEND_LIMIT = TREE_PATH_MAX_ELEMENT_COUNT
FILE_COUNT_ABOVE_BACKEND_LIMIT = TREE_PATH_MAX_ELEMENT_COUNT + 1

TREE_ASSET_FRONTEND_FOLDER_NAME = "frontend_limit"
TREE_ASSET_BACKEND_FOLDER_NAME = "backend_limit"
TREE_ASSET_BACKEND_PASSED_FOLDER_NAME = "backend_limit_passed"


ASSET_FILE_NAME = "tree_file.txt"


def _upload_test_assets(count: int, folder: Path | None = None):
    if folder is None:
        folder = Path()
    for i in range(count):
        upload_asset(
            ASSET_FILE_NAME,
            str(Path("//api-upload") / folder / Path(f"{i}{ASSET_FILE_NAME}")),
        )


def _files_tree(
    search_string: str, directory: str, after: str | None = None
) -> GetFilesTreeResponse:
    response = requests.get(
        f"{FILES_ENDPOINT}/tree",
        params=GetFilesTreeQuery(
            search_string=search_string,
            node_path=directory,
            query_id=fetch_query_id(),
            after=after,
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    tree_models = GetFilesTreeResponse.model_validate(response.json())
    return tree_models


class TestFileTree:
    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        _upload_test_assets(FILE_COUNT_TOP_LEVEL)
        _upload_test_assets(
            FILE_COUNT_BELOW_FRONTEND_LIMIT, Path(TREE_ASSET_FRONTEND_FOLDER_NAME)
        )
        _upload_test_assets(
            FILE_COUNT_BELOW_BACKEND_LIMIT, Path(TREE_ASSET_BACKEND_FOLDER_NAME)
        )
        _upload_test_assets(
            FILE_COUNT_ABOVE_BACKEND_LIMIT, Path(TREE_ASSET_BACKEND_PASSED_FOLDER_NAME)
        )
        # We intentionally don't wait here for the files to be processed,
        # because for the tree view the indexing state of the files
        # is quite irrelevant...
        fetch_files_from_api(
            search_string="*",
            expected_no_of_files=(
                FILE_COUNT_TOP_LEVEL
                + FILE_COUNT_BELOW_FRONTEND_LIMIT
                + FILE_COUNT_BELOW_BACKEND_LIMIT
                + FILE_COUNT_ABOVE_BACKEND_LIMIT
            ),
            expected_state=None,
        )

    def test_unfiltered_level(self):
        tree_models = _files_tree("*", "/")

        assert len(tree_models.nodes) == 1
        assert str(tree_models.nodes[0].full_path) == "//api-upload"
        assert tree_models.nodes[0].file_count == (
            FILE_COUNT_TOP_LEVEL
            + FILE_COUNT_BELOW_FRONTEND_LIMIT
            + FILE_COUNT_BELOW_BACKEND_LIMIT
            + FILE_COUNT_ABOVE_BACKEND_LIMIT
        )

    def test_filtered_level(self):
        search_string = build_search_string("*", "filename", f"0{ASSET_FILE_NAME}")
        tree_models = _files_tree(search_string, "/")

        assert len(tree_models.nodes) == 1
        assert str(tree_models.nodes[0].full_path) == "//api-upload"
        assert tree_models.nodes[0].file_count == 4

    def test_below_frontend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}",
        )

        assert len(tree_models.nodes) == FILE_COUNT_BELOW_FRONTEND_LIMIT
        assert (
            str(tree_models.nodes[0].full_path)
            == f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.nodes[0].file_count == 0

    def test_below_backend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_FOLDER_NAME}",
        )

        # We expect the backend to truncate to one above frontend limit,
        # so the frontend knows if there are more than the limit
        assert len(tree_models.nodes) == FILE_COUNT_BELOW_BACKEND_LIMIT
        assert (
            str(tree_models.nodes[0].full_path)
            == f"//api-upload/{TREE_ASSET_BACKEND_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.nodes[0].file_count == 0

    def test_above_backend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}",
        )

        # With FILE_COUNT_ABOVE_BACKEND_LIMIT files, the backend returns the first
        # page of TREE_PATH_MAX_ELEMENT_COUNT nodes and a next_page_cursor.
        assert len(tree_models.nodes) == FILE_COUNT_BELOW_BACKEND_LIMIT
        assert (
            str(tree_models.nodes[0].full_path)
            == f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.nodes[0].file_count == 0
        assert tree_models.next_page_cursor is not None

    def test_cursor_pagination(self):
        # Upload exactly FILE_COUNT_ABOVE_BACKEND_LIMIT files so the backend must
        # paginate. The first page must return TREE_PATH_MAX_ELEMENT_COUNT nodes
        # and a cursor; the second page must return the remaining node(s) and no
        # further cursor, and the two pages together must cover all files without
        # duplicates.
        first_page = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}",
        )

        assert len(first_page.nodes) == TREE_PATH_MAX_ELEMENT_COUNT
        assert first_page.next_page_cursor is not None

        second_page = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}",
            after=first_page.next_page_cursor,
        )

        remaining = FILE_COUNT_ABOVE_BACKEND_LIMIT - TREE_PATH_MAX_ELEMENT_COUNT
        assert len(second_page.nodes) == remaining
        assert second_page.next_page_cursor is None

        # Combined pages cover all files without duplicates or gaps.
        all_paths = {str(n.full_path) for n in first_page.nodes} | {
            str(n.full_path) for n in second_page.nodes
        }
        assert len(all_paths) == FILE_COUNT_ABOVE_BACKEND_LIMIT

    def test_0_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}/0{ASSET_FILE_NAME}",
        )

        assert len(tree_models.nodes) == 0

    def test_invalid_path(self):
        tree_models = _files_tree("*", "//api-upload/invalid")

        assert len(tree_models.nodes) == 0

    def test_invalid_query(self):
        with pytest.raises(HTTPError):
            _files_tree("full_path:/(", "//api-upload/")


def _files_tree_spine(search_string: str, full_path: str) -> GetFilesTreeResponse:
    response = requests.get(
        f"{FILES_ENDPOINT}/tree/spine",
        params=GetFilesTreeSpineQuery(
            search_string=search_string,
            full_path=full_path,
            query_id=fetch_query_id(),
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return GetFilesTreeResponse.model_validate(response.json())


class TestFileTreeSpine:
    SPINE_FILE_NAME = "spine_test_file.txt"
    SPINE_FOLDER = "a/b/c"

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_bytes_asset(
            b"spine test file",
            f"//api-upload/{self.SPINE_FOLDER}/{self.SPINE_FILE_NAME}",
        )
        fetch_files_from_api(
            search_string=f"filename:{self.SPINE_FILE_NAME}",
            expected_no_of_files=1,
            expected_state=None,
        )

    def test_spine_returns_all_ancestors(self):
        full_path = f"//api-upload/{self.SPINE_FOLDER}/{self.SPINE_FILE_NAME}"
        result = _files_tree_spine("*", full_path)

        paths = [str(n.full_path) for n in result.nodes]
        assert "//api-upload" in paths
        assert "//api-upload/a" in paths
        assert "//api-upload/a/b" in paths
        assert "//api-upload/a/b/c" in paths
        assert full_path in paths

        leaf = next(n for n in result.nodes if str(n.full_path) == full_path)
        assert leaf.file_id is not None

        assert result.next_page_cursor is None

    def test_spine_empty_for_nonexistent_path(self):
        result = _files_tree_spine("*", "//api-upload/does/not/exist.txt")
        assert result.nodes == []

    def test_spine_respects_search_filter(self):
        full_path = f"//api-upload/{self.SPINE_FOLDER}/{self.SPINE_FILE_NAME}"
        result = _files_tree_spine("filename:__no_match_xyz__", full_path)
        assert result.nodes == []


def test_spine_shallow_path():
    shallow_file = "spine_shallow.txt"
    upload_bytes_asset(b"spine shallow test file", f"//api-upload/{shallow_file}")
    fetch_files_from_api(
        search_string=f"filename:{shallow_file}",
        expected_no_of_files=1,
        expected_state=None,
    )

    result = _files_tree_spine("*", f"//api-upload/{shallow_file}")
    paths = [str(n.full_path) for n in result.nodes]
    assert "//api-upload" in paths
    assert f"//api-upload/{shallow_file}" in paths
    assert len(result.nodes) == 2
