"""Integration tests for the /v1/aitools/...

REST endpoints and the AI persist path.
"""

import pytest
import requests
from api.routers.ai import ContextHistoryResponse

from utils.ai_helpers import create_ai_context, run_agent
from utils.consts import AI_ENDPOINT, AITOOLS_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
)
from utils.polling import poll_until
from utils.upload_asset import upload_many_assets

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")


class TestAiToolService:
    asset_list = ["knn1.txt", "knn2.txt", "knn3.txt", "knn4.txt", "knn5.txt"]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)
        fetch_files_from_api(
            search_string="*",
            expected_no_of_files=len(self.asset_list),
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE
            * len(self.asset_list),
        )

    def test_execute_query_returns_files(self):
        response = requests.get(
            f"{AITOOLS_ENDPOINT}/files/execute-query",
            params={"query_string": "network"},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) > 0
        for file_entry in data["files"]:
            assert "file_id" in file_entry
            assert "text" in file_entry

    def test_execute_query_invalid_query_returns_error(self):
        response = requests.get(
            f"{AITOOLS_ENDPOINT}/files/execute-query",
            params={"query_string": "]]]invalid[[["},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code >= 400

    def test_get_file_returns_available_fields(self):
        # Fetch a known file ID via the search endpoint
        search_response = requests.get(
            f"{AITOOLS_ENDPOINT}/files/execute-query",
            params={"query_string": "*"},
            timeout=REQUEST_TIMEOUT,
        )
        search_response.raise_for_status()
        files = search_response.json()["files"]
        assert files, "expected at least one file from execute-query"
        file_id = files[0]["file_id"]

        response = requests.get(
            f"{AITOOLS_ENDPOINT}/files/{file_id}",
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert "available_fields" in data
        assert len(data["available_fields"]) > 0
        for field in data["available_fields"]:
            assert "name" in field
            assert "description" in field

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
