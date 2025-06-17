from pathlib import Path

import pytest
import requests
from api.routers.files import GetFilesTreeQuery, GetFilesTreeResponse
from common.file.file_repository import (
    TREE_PATH_BUCKET_SIZE,
    TREE_PATH_MAX_ELEMENT_COUNT,
)
from requests import HTTPError

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import build_search_string, fetch_query_id
from utils.upload_asset import upload_asset

FILE_COUNT_TOP_LEVEL = 3
FILE_COUNT_BELOW_FRONTEND_LIMIT = TREE_PATH_MAX_ELEMENT_COUNT
FILE_COUNT_BELOW_BACKEND_LIMIT = TREE_PATH_BUCKET_SIZE
FILE_COUNT_ABOVE_BACKEND_LIMIT = TREE_PATH_BUCKET_SIZE + 1

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


def _files_tree(search_string: str, directory: str) -> GetFilesTreeResponse:
    response = requests.get(
        f"{FILES_ENDPOINT}/tree",
        params=GetFilesTreeQuery(
            search_string=search_string,
            node_path=directory,
            query_id=fetch_query_id(),
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
        # We intentionally don't wait here, because for the tree view
        # the indexing state of the files is quite irrelevant...
        #
        # if we'd need to wait here we should use something like
        # this:
        #
        # fetch_files_from_api(
        #    search_string="*",
        #    expected_no_of_files=(
        #        FILE_COUNT_TOP_LEVEL
        #        + FILE_COUNT_BELOW_FRONTEND_LIMIT
        #        + FILE_COUNT_BELOW_BACKEND_LIMIT
        #        + FILE_COUNT_ABOVE_BACKEND_LIMIT
        #    ),
        # )

    def test_unfiltered_level(self):
        tree_models = _files_tree("*", "/")

        assert len(tree_models.root) == 1
        assert str(tree_models.root[0].full_path) == "//api-upload"
        assert tree_models.root[0].file_count == (
            FILE_COUNT_TOP_LEVEL
            + FILE_COUNT_BELOW_FRONTEND_LIMIT
            + FILE_COUNT_BELOW_BACKEND_LIMIT
            + FILE_COUNT_ABOVE_BACKEND_LIMIT
        )

    def test_filtered_level(self):
        search_string = build_search_string("*", "filename", f"0{ASSET_FILE_NAME}")
        tree_models = _files_tree(search_string, "/")

        assert len(tree_models.root) == 1
        assert str(tree_models.root[0].full_path) == "//api-upload"
        assert tree_models.root[0].file_count == 4

    def test_below_frontend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}",
        )

        assert len(tree_models.root) == FILE_COUNT_BELOW_FRONTEND_LIMIT
        assert (
            str(tree_models.root[0].full_path)
            == f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.root[0].file_count == 1

    def test_below_backend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_FOLDER_NAME}",
        )

        # We expect the backend to truncate to one above frontend limit,
        # so the frontend knows if there are more than the limit
        assert len(tree_models.root) == FILE_COUNT_BELOW_BACKEND_LIMIT
        assert (
            str(tree_models.root[0].full_path)
            == f"//api-upload/{TREE_ASSET_BACKEND_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.root[0].file_count == 1

    def test_above_backend_limit_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}",
        )

        # We expect the backend to truncate to one above the limit on the frontend
        assert len(tree_models.root) == FILE_COUNT_BELOW_BACKEND_LIMIT
        assert (
            str(tree_models.root[0].full_path)
            == f"//api-upload/{TREE_ASSET_BACKEND_PASSED_FOLDER_NAME}/0{ASSET_FILE_NAME}"
        )
        assert tree_models.root[0].file_count == 1

    def test_0_entries(self):
        tree_models = _files_tree(
            "*",
            f"//api-upload/{TREE_ASSET_FRONTEND_FOLDER_NAME}/0{ASSET_FILE_NAME}",
        )

        assert len(tree_models.root) == 0

    def test_invalid_path(self):
        tree_models = _files_tree("*", "//api-upload/invalid")

        assert len(tree_models.root) == 0

    def test_invalid_query(self):
        with pytest.raises(HTTPError):
            _files_tree("full_path:/(", "//api-upload/")
