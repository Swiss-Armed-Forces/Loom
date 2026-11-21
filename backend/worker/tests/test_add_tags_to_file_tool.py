from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common.dependencies import get_file_repository

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.tasks.add_tags_to_file_tool import add_tags_to_file_tool_task


def _task() -> MagicMock:
    """Stands in for the bound task.

    Both branches under test raise before the task hands the write on, so nothing of the
    real one is reached.
    """
    return MagicMock(spec=AiContextProcessingTask)


def test_a_file_id_that_is_not_a_uuid_is_reported_as_a_retryable_error():
    """ToolService maps ValueError to a ModelRetry, which is what gives the model a
    chance to correct an id it invented."""
    with pytest.raises(ValueError, match="must be a valid UUID"):
        add_tags_to_file_tool_task(_task(), "not-a-uuid", ["rhine-2024"], uuid4())


def test_a_missing_file_is_reported_as_a_lookup_error():
    """The file is looked up before the write is handed on, so a tag write against a
    file that does not exist fails rather than mutating nothing."""
    cast(MagicMock, get_file_repository()).get_by_id.return_value = None

    with pytest.raises(LookupError, match="not found"):
        add_tags_to_file_tool_task(_task(), str(uuid4()), ["rhine-2024"], uuid4())
