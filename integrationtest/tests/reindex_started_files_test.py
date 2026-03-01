import logging
from typing import Callable

import pytest
from common.dependencies import get_celery_app, get_file_repository
from worker.periodic.tasks.reindex_started_files import (
    reindex_started_files,
)

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets

logger = logging.getLogger(__name__)


def _get_fully_qualified_name(obj: type | Callable):
    module_name = obj.__module__
    qualified_name = obj.__qualname__
    return f"{module_name}.{qualified_name}"


ASSET_LIST = ["empty_file.txt"]


def _set_files_to_started_state():
    """simulate: file stuck in started state"""

    # get all files
    search_string = "*"
    file_count = len(ASSET_LIST)
    files = fetch_files_from_api(
        search_string=search_string, expected_no_of_files=file_count
    )

    # set to started state
    file_repository = get_file_repository()
    for file_entry in files.files:
        file = file_repository.get_by_id(file_entry.file_id)
        assert file is not None
        file.state = "started"
        file_repository.update(file, include={"state"})

    # verify that files are in started state
    fetch_files_from_api(
        search_string=search_string,
        expected_no_of_files=file_count,
        expected_state="started",
    )


@pytest.fixture(scope="function", autouse=True)
def setup_testfiles():
    upload_many_assets(asset_names=ASSET_LIST)

    # wait for assets to be processes
    search_string = "*"
    file_count = len(ASSET_LIST)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=file_count)
    _set_files_to_started_state()


def test_reindex_started_files():
    fully_qualified_name = _get_fully_qualified_name(reindex_started_files)

    get_celery_app().send_task(
        fully_qualified_name,
    ).forget()

    search_string = "*"
    file_count = len(ASSET_LIST)
    files = fetch_files_from_api(
        search_string=search_string, expected_no_of_files=file_count
    )
    # check reindex_count
    file_repository = get_file_repository()
    for file_entry in files.files:
        file = file_repository.get_by_id(file_entry.file_id)
        assert file is not None
        assert file.reindex_count == 1
