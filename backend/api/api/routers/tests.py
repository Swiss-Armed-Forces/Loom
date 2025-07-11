import logging

from common.dependencies import get_task_scheduling_service
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


router = APIRouter()

default_task_scheduling_service = Depends(get_task_scheduling_service)


@router.post("/dispatch_sigkill_pgroup_task")
def dispatch_sigkill_pgroup_task(
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.sigkill_prgoup()
