"""Translation router."""

import logging

from common.dependencies import (
    get_task_scheduling_service,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

logger = logging.getLogger(__name__)

default_task_scheduling_service = Depends(get_task_scheduling_service)


class TranslateAllRequest(BaseModel):
    """Query to filter files."""

    lang: str
    query: QueryParameters


@router.post("", status_code=202)
def translate_files_on_demand(
    translation_request: TranslateAllRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_translate_files(
        query=translation_request.query,
        lang=translation_request.lang,
    )
