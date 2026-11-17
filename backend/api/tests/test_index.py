import pytest
from common.dependencies import get_task_scheduling_service
from common.services.task_scheduling_service import (
    MAX_ADDITIONAL_RECURSION_DEPTH,
    IndexingPriority,
)
from common.settings import settings
from fastapi.testclient import TestClient


def test_index_files_dispatches_the_requested_depth(client: TestClient):
    response = client.post(
        "/v1/files/index",
        json={"query": {"search_string": "*"}, "additional_recursion_depth": 2},
    )

    assert response.status_code == 202
    get_task_scheduling_service().dispatch_reindex_files.assert_called_once()
    kwargs = get_task_scheduling_service().dispatch_reindex_files.call_args.kwargs
    assert kwargs["additional_recursion_depth"] == 2
    # A sweep over a whole result set must not outrank an interactive re-index.
    assert kwargs["priority"] == IndexingPriority.MEDIUM


def test_index_files_falls_back_to_the_configured_depth(client: TestClient):
    """The field is optional, so a client written before it existed still works."""
    response = client.post("/v1/files/index", json={"query": {"search_string": "*"}})

    assert response.status_code == 202
    kwargs = get_task_scheduling_service().dispatch_reindex_files.call_args.kwargs
    assert kwargs["additional_recursion_depth"] == settings.indexing_max_recursion_depth


@pytest.mark.parametrize(
    "additional_recursion_depth", [-1, MAX_ADDITIONAL_RECURSION_DEPTH + 1]
)
def test_index_files_rejects_a_depth_outside_the_bounds(
    client: TestClient, additional_recursion_depth: int
):
    """This depth applies to every file the query matches, so one request out of bounds
    multiplies the whole corpus."""
    response = client.post(
        "/v1/files/index",
        json={
            "query": {"search_string": "*"},
            "additional_recursion_depth": additional_recursion_depth,
        },
    )

    assert response.status_code == 422
    get_task_scheduling_service().dispatch_reindex_files.assert_not_called()
