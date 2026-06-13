from common.dependencies import get_complete_estimate_service
from common.services.complete_estimate_service import (
    CompleteEstimateResult,
    CompleteEstimateService,
)
from fastapi import APIRouter, Depends

router = APIRouter()

default_complete_estimate_service = Depends(get_complete_estimate_service)


@router.get("")
def get_complete_estimate(
    complete_estimate_service: CompleteEstimateService = default_complete_estimate_service,
) -> CompleteEstimateResult:
    return complete_estimate_service.get_cached_result()
