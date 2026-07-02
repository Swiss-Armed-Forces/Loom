import logging

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_task_scheduling_service,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from common.settings import settings
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_file_scheduling_service = Depends(get_file_scheduling_service)
default_task_scheduling_service = Depends(get_task_scheduling_service)


class ImageDescriptionRequest(BaseModel):
    """Query to filter files."""

    query: QueryParameters
    system_prompt: str | None = None


@router.get("/system_prompt", status_code=200)
def get_system_prompt() -> str:
    return settings.llm.vision.system_prompt


@router.post("", status_code=202)
def describe_images_on_demand(
    image_description_request: ImageDescriptionRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_describe_images(
        query=image_description_request.query,
        system_prompt=image_description_request.system_prompt,
    )
