import json

import pytest
import requests
from api.routers.ai import ContextHistoryResponse

from utils.ai_helpers import create_ai_context, run_agent
from utils.consts import AI_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
)
from utils.polling import poll_until
from utils.upload_asset import upload_many_assets


def test_create_context():
    create_ai_context()


@pytest.mark.usefixtures("disable_periodic_tasks")
class TestChatbot:
    # A single file is sufficient to exercise the chatbot pipeline; extra files
    # (knn2-knn5) were removed to keep the test fast.
    asset_list = [
        "knn1.txt",
    ]

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def setup_testfiles(cls):
        upload_many_assets(asset_names=cls.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(cls.asset_list)
        fetch_files_from_api(
            search_string=search_string,
            expected_no_of_files=file_count,
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE * len(cls.asset_list),
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

    @pytest.mark.flaky(reruns=3)
    def test_persist_question_appears_in_history(self):
        ai_context = create_ai_context()
        context_id = ai_context.context_id
        question = "What topics are covered in the documents?"

        stream = run_agent(ai_context_id=context_id, question=question)
        # Consume the full SSE stream so the agent completes
        for _ in stream.iter_lines(decode_unicode=True):
            pass

        def fetch_history() -> ContextHistoryResponse:
            resp = requests.get(
                f"{AI_ENDPOINT}/{context_id}/history",
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return ContextHistoryResponse.model_validate(resp.json())

        # The question is persisted asynchronously via a Celery task.
        history = poll_until(
            fetch=fetch_history,
            predicate=lambda h: len(h.questions) > 0,
            description="question to appear in history",
        )

        assert len(history.questions) == 1
        assert history.questions[0].question == question
        assert history.questions[0].answer
