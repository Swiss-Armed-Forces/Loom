import logging
from datetime import timedelta
from typing import Callable

import pytest
from common.dependencies import get_celery_app
from worker.periodic.tasks.hide_old_uploaded_files import hide_old_uploaded_files_task

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets

logger = logging.getLogger(__name__)


def _get_fully_qualified_name(obj: type | Callable):
    module_name = obj.__module__
    qualified_name = obj.__qualname__
    return f"{module_name}.{qualified_name}"


ASSET_LIST = ["empty_file.txt"]


@pytest.fixture(scope="function", autouse=True)
def setup_testfiles():
    upload_many_assets(asset_names=ASSET_LIST)

    # wait for assets to be processes
    search_string = "*"
    file_count = len(ASSET_LIST)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=file_count)


def test_hide_old_uploaded_files_task_does_hide_when_in_range():
    test_time = timedelta(seconds=1)
    fully_qualified_name = _get_fully_qualified_name(hide_old_uploaded_files_task)

    get_celery_app().send_task(
        fully_qualified_name,
        args=[
            test_time,
        ],
    ).forget()

    search_string = "* AND hidden:true"
    file_count = len(ASSET_LIST)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=file_count)


def test_hide_old_uploaded_files_task_does_not_hide_when_not_in_range():
    test_time = timedelta(days=1)
    fully_qualified_name = _get_fully_qualified_name(hide_old_uploaded_files_task)

    get_celery_app().send_task(
        fully_qualified_name,
        args=[
            test_time,
        ],
    ).forget()

    search_string = "* AND hidden:false"
    file_count = len(ASSET_LIST)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=file_count)
