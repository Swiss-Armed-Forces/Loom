# pylint: disable=duplicate-code
from typing import Callable

import pytest
import requests
from api.routers.files import ImageDescriptionFileRequest
from api.routers.image_description import ImageDescriptionRequest
from common.services.query_builder import QueryParameters
from pydantic import BaseModel
from requests import Response

from utils.consts import FILES_ENDPOINT, IMAGE_DESCRIPTION_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    build_search_string,
    fetch_query_id,
    get_file_by_name,
)
from utils.upload_asset import upload_asset


class ImageDescriptionFileTest(BaseModel):
    file_id: str
    name: str


IMAGE_DESCRIPTION_TESTCASES = [
    (
        "1.png",
        DEFAULT_MAX_WAIT_TIME_PER_FILE * 3,
    ),
    (
        "ocr.jpg",
        DEFAULT_MAX_WAIT_TIME_PER_FILE * 3,
    ),
]


def _on_demand_image_description_by_query(
    query: QueryParameters,
):
    response: Response = requests.post(
        f"{IMAGE_DESCRIPTION_ENDPOINT}/",
        json=ImageDescriptionRequest(query=query).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _on_demand_image_description_by_file(
    file: ImageDescriptionFileTest,
):
    response: Response = requests.post(
        f"{FILES_ENDPOINT}/{file.file_id}/image_description/",
        json=ImageDescriptionFileRequest().model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _image_description_testcase(
    on_demand_image_description: Callable[[ImageDescriptionFileTest], None],
    file_name: str,
    max_wait_time_per_file: int | None = None,
):
    upload_asset(file_name)

    # wait for file to be processed
    file = get_file_by_name(
        file_name,
        max_wait_time_per_file=max_wait_time_per_file,
    )

    # create a custom model to generalize the calls
    image_description_file = ImageDescriptionFileTest(
        file_id=str(file.file_id), name=file.name
    )

    # demand image description
    on_demand_image_description(image_description_file)

    # Wait until celery is idle AND the description has been persisted.
    get_file_by_name(
        file_name,
        max_wait_time_per_file=max_wait_time_per_file,
        wait_for_celery_idle=True,
        checker=lambda f: f.image_description is not None,
    )


@pytest.mark.parametrize(
    "file_name, max_wait_time_per_file",
    IMAGE_DESCRIPTION_TESTCASES,
)
def test_on_demand_image_description_by_file(
    file_name: str, max_wait_time_per_file: int | None
):
    _image_description_testcase(
        on_demand_image_description=_on_demand_image_description_by_file,
        file_name=file_name,
        max_wait_time_per_file=max_wait_time_per_file,
    )


@pytest.mark.parametrize(
    "file_name, max_wait_time_per_file",
    IMAGE_DESCRIPTION_TESTCASES,
)
def test_on_demand_image_description_by_query(
    file_name: str, max_wait_time_per_file: int | None
):
    def on_demand_function(file: ImageDescriptionFileTest):
        _on_demand_image_description_by_query(
            QueryParameters(
                query_id=fetch_query_id(),
                search_string=build_search_string(
                    search_string="*", field="full_name", field_value=file.name
                ),
            ),
        )

    _image_description_testcase(
        on_demand_image_description=on_demand_function,
        file_name=file_name,
        max_wait_time_per_file=max_wait_time_per_file,
    )
