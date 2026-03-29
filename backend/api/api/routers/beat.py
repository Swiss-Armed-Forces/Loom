import logging
from typing import Annotated

from common.celery_app import get_beat_schedule
from common.dependencies import get_task_scheduling_service
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AfterValidator, WithJsonSchema

router = APIRouter()

logger = logging.getLogger(__name__)


def _validate_schedule_name(v: str) -> str:
    if v not in get_beat_schedule():
        raise ValueError(f"Invalid schedule name: {v}")
    return v


BeatScheduleName = Annotated[
    str,
    AfterValidator(_validate_schedule_name),
    WithJsonSchema({"type": "string", "enum": list(get_beat_schedule().keys())}),
]

default_task_scheduling_service = Depends(get_task_scheduling_service)


@router.post("/{schedule_name}", status_code=204)
def trigger_scheduled_task(
    schedule_name: BeatScheduleName,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
) -> None:
    """Manually trigger a scheduled task by name.

    Args:
        schedule_name: The name of the scheduled task from beat_schedule.
    """
    logger.info("Triggering scheduled task: %s", schedule_name)

    try:
        task_scheduling_service.trigger_scheduled_task(schedule_name)
    except KeyError as ex:
        raise HTTPException(
            status_code=404, detail=f"Schedule '{schedule_name}' not found"
        ) from ex
