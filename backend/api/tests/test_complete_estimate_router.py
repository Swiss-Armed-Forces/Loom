from common.dependencies import get_complete_estimate_service
from common.services.complete_estimate_service import CompleteEstimateResult
from fastapi.testclient import TestClient


def test_get_complete_estimate(client: TestClient):
    mock = get_complete_estimate_service()
    mock.get_cached_result.return_value = CompleteEstimateResult(
        estimate_timestamp=9999,
        files_pending=42,
    )

    response = client.get("/v1/complete-estimate")
    response.raise_for_status()
    result = CompleteEstimateResult.model_validate(response.json())

    assert result.estimate_timestamp == 9999
    assert result.files_pending == 42


def test_get_complete_estimate_no_data(client: TestClient):
    mock = get_complete_estimate_service()
    mock.get_cached_result.return_value = CompleteEstimateResult(
        estimate_timestamp=None,
        files_pending=None,
    )

    response = client.get("/v1/complete-estimate")
    response.raise_for_status()
    result = CompleteEstimateResult.model_validate(response.json())

    assert result.estimate_timestamp is None
    assert result.files_pending is None
