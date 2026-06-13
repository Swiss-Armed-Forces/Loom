import pytest
import requests
from common.dependencies import get_celery_app
from common.services.complete_estimate_service import CompleteEstimateResult
from worker.periodic.compute_complete_estimate_task import (
    compute_complete_estimate_task,
)

from utils.consts import COMPLETE_ESTIMATE_ENDPOINT, REQUEST_TIMEOUT


def _get_complete_estimate() -> CompleteEstimateResult:
    response = requests.get(COMPLETE_ESTIMATE_ENDPOINT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return CompleteEstimateResult.model_validate(response.json())


class TestCompleteEstimate:

    @pytest.fixture(autouse=True)
    def trigger_task(self):
        # Run the periodic task so Redis reflects the current system state
        get_celery_app().send_task(compute_complete_estimate_task.name).get(
            timeout=REQUEST_TIMEOUT
        )

    def test_get_complete_estimate_when_idle(self):
        result = _get_complete_estimate()
        assert result.files_pending == 0
        assert result.estimate_timestamp is None
