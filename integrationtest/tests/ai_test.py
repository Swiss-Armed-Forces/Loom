import json

import pytest

from utils.ai_helpers import create_ai_context, run_agent
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
)
from utils.upload_asset import upload_many_assets


def test_create_context():
    create_ai_context()


class TestChatbot:
    # A single file is sufficient to exercise the chatbot pipeline; extra files
    # (knn2-knn5) were removed to keep the test fast.
    asset_list = [
        "knn1.txt",
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

    @pytest.mark.flaky(reruns=3)
    def test_chatbot(self):
        ai_context = create_ai_context()

        response = run_agent(
            ai_context_id=ai_context.context_id,
            question="What is network security?",
        )

        event_types: list[str] = []
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data = json.loads(line[len("data:") :].strip())
            if "type" in data:
                event_types.append(data["type"])

        assert "TEXT_MESSAGE_START" in event_types
        assert "TEXT_MESSAGE_END" in event_types
