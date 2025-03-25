import json

import pytest
import requests
from common.dependencies import get_redis_client
from pydantic import BaseModel
from requests import Response

from utils.consts import AI_ENDPOINT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_by_name,
)
from utils.upload_asset import upload_many_assets


class SummarizationFileTest(BaseModel):
    file_id: str
    name: str


KNN_QUESTION = "Explain network security concisely."


class TestRag:
    asset_list = [
        "knn1.txt",
        "knn2.txt",
        "knn3.txt",
        "knn4.txt",
        "knn5.txt",
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string,
            expected_no_of_files=file_count,
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE
            * len(self.asset_list),
        )

    @pytest.mark.skip("This needs refactoring")
    def test_chatbot(self):
        context_response: Response = requests.post(
            AI_ENDPOINT,
            timeout=DEFAULT_MAX_WAIT_TIME_PER_FILE,
        )

        context_response.raise_for_status()
        context = context_response.json()
        context_id = context["context_id"]

        pubsub = get_redis_client().pubsub()
        pubsub.subscribe(context_id)

        response: Response = requests.post(
            f"{AI_ENDPOINT}/{context_id}/process_question?question={KNN_QUESTION}",
            timeout=DEFAULT_MAX_WAIT_TIME_PER_FILE,
        )

        response.raise_for_status()

        output = ""
        citations = []
        for m in pubsub.listen():
            if m["type"] != "message":
                continue

            message = json.loads(m["data"])["message"]
            t = message["type"]
            if t == "chatBotToken":
                output += message["token"]
            if t == "chatBotCitation":
                citations.append(message["file_id"])
                pubsub.close()

        assert len(output) > 0
        assert str(get_file_by_name("knn1.txt").file_id) in citations
