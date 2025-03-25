# pylint: disable=duplicate-code
from typing import Callable

import pytest
import requests
from api.models.query_model import QueryModel
from api.routers.files import SummarizeFileRequest
from api.routers.summarization import SummarizationRequest
from pydantic import BaseModel
from requests import Response

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT, SUMMARIZATION_ENDPOINT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    build_search_string,
    get_file_by_name,
)
from utils.upload_asset import upload_bytes_asset


class SummarizationFileTest(BaseModel):
    file_id: str
    name: str


LONG_TEXT = (
    "He was digging in his garden--digging, too, "
    "in his own mind, laboriously turning up the substance of his "
    "thought. Death--and he drove in his spade once, and again, and "
    "yet again. And all our yesterdays have lighted fools the way "
    "to dusty death. A convincing thunder rumbled through the words. "
    "He lifted another spadeful of earth. Why had Linda died? Why "
    "had she been allowed to become gradually less than human and "
    "at last... He shuddered."
)

SUMMARIZATION_TESTCASES = [
    #  "system_prompt, document_string, max_wait_time_per_file"
    #
    # The next line should come back once we fixed the queue idle
    # waiting.
    # (None, "Short test case.", None),
    (
        None,
        LONG_TEXT,
        DEFAULT_MAX_WAIT_TIME_PER_FILE * 3,
    ),
    (
        "You are a pirate",
        LONG_TEXT,
        DEFAULT_MAX_WAIT_TIME_PER_FILE * 3,
    ),
]


def _on_demand_summarize_by_query(query: QueryModel, system_prompt: str | None = None):
    response: Response = requests.post(
        f"{SUMMARIZATION_ENDPOINT}/",
        json=SummarizationRequest(
            query=query, system_prompt=system_prompt
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _on_demand_summarize_by_file(
    file: SummarizationFileTest, system_prompt: str | None = None
):
    response: Response = requests.post(
        f"{FILES_ENDPOINT}/{file.file_id}/summarize/",
        json=SummarizeFileRequest(system_prompt=system_prompt).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _summarization_testcase(
    on_demand_summarization: Callable[[SummarizationFileTest, str | None], None],
    document_string: str,
    system_prompt: str | None,
    max_wait_time_per_file: int | None = None,
):
    file_name = "text.txt"
    upload_bytes_asset(document_string.encode(), file_name)

    # wait for file to be processed
    file = get_file_by_name(
        file_name,
        max_wait_time_per_file=max_wait_time_per_file,
    )

    # create a custom model to generalize the calls
    summarization_file = SummarizationFileTest(
        file_id=str(file.file_id), name=file.name
    )

    # demand summarization
    on_demand_summarization(summarization_file, system_prompt)
    file = get_file_by_name(
        file_name,
        max_wait_time_per_file=max_wait_time_per_file,
    )
    assert file.summary is not None


@pytest.mark.parametrize(
    "system_prompt, document_string, max_wait_time_per_file",
    SUMMARIZATION_TESTCASES,
)
def test_on_demand_summarization_by_file(
    system_prompt: str | None, document_string: str, max_wait_time_per_file: int | None
):
    _summarization_testcase(
        on_demand_summarization=_on_demand_summarize_by_file,
        document_string=document_string,
        system_prompt=system_prompt,
        max_wait_time_per_file=max_wait_time_per_file,
    )


@pytest.mark.parametrize(
    "system_prompt, document_string, max_wait_time_per_file",
    SUMMARIZATION_TESTCASES,
)
def test_on_demand_summarization_by_query(
    system_prompt: str | None, document_string: str, max_wait_time_per_file: int | None
):
    def on_demand_function(file: SummarizationFileTest, system_prompt: str | None):
        _on_demand_summarize_by_query(
            QueryModel(
                search_string=build_search_string(
                    search_string="*", field="full_name", field_value=file.name
                )
            ),
            system_prompt=system_prompt,
        )

    _summarization_testcase(
        on_demand_summarization=on_demand_function,
        document_string=document_string,
        system_prompt=system_prompt,
        max_wait_time_per_file=max_wait_time_per_file,
    )
