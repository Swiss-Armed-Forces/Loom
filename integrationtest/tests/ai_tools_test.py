"""Integration tests for the AI document tools against a real Elasticsearch.

The tools are exercised through their Celery tasks — the same entry point the chatbot's
``ToolService`` dispatches to.
"""

from uuid import uuid4

import pytest
from common.ai_context.tool_models import ExecuteQueryResult, GetFileResult
from common.dependencies import get_celery_app
from worker.ai.tasks.execute_query_tool import execute_query_tool_task
from worker.ai.tasks.get_file_tool import get_file_tool_task

from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
)
from utils.upload_asset import upload_many_assets

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")

GET_TIMEOUT = 120


def _execute_query(query_string: str) -> ExecuteQueryResult:
    return (
        get_celery_app()
        .send_task(
            execute_query_tool_task.name,
            args=[query_string, uuid4(), None],
        )
        .get(timeout=GET_TIMEOUT)
    )


def _get_file(file_id: str) -> GetFileResult:
    return (
        get_celery_app()
        .send_task(
            get_file_tool_task.name,
            args=[file_id, uuid4()],
        )
        .get(timeout=GET_TIMEOUT)
    )


class TestAiTools:
    # The tools are read-only, so a single indexed file is enough for the whole
    # class to share.
    asset_list = ["knn1.txt"]

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def setup_testfiles(cls):
        upload_many_assets(asset_names=cls.asset_list)
        fetch_files_from_api(
            search_string="*",
            expected_no_of_files=len(cls.asset_list),
            max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE * len(cls.asset_list),
        )

    def test_execute_query_returns_files(self):
        result = _execute_query("network")

        assert result.files
        for file_entry in result.files:
            assert file_entry.file_id
            assert file_entry.text

    def test_execute_query_invalid_query_raises(self):
        # Elasticsearch rejects the query string; the tool must surface that as a
        # ValueError the agent can recover from, not as an opaque backend error.
        with pytest.raises(ValueError):
            _execute_query("]]]invalid[[[")

    def test_get_file_returns_available_fields(self):
        query_result = _execute_query("*")
        assert query_result.files, "expected at least one file from execute_query"
        file_id = query_result.files[0].file_id

        result = _get_file(file_id)

        assert result.file_id == file_id
        assert result.full_path
        assert result.available_fields
        for field in result.available_fields:
            assert field.name
            assert field.description
