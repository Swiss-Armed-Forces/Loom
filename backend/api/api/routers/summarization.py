"""Summarization router."""

import logging

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_task_scheduling_service,
)
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.models.query_model import QueryModel
from api.settings import settings

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_file_scheduling_service = Depends(get_file_scheduling_service)
default_task_scheduling_service = Depends(get_task_scheduling_service)


class SummarizationRequest(BaseModel):
    """Query to filter files."""

    query: QueryModel
    system_prompt: str | None = None


@router.get("/system_prompt", status_code=200)
def get_system_prompt() -> str:
    return settings.llm_summarize_system_prompt


@router.post("/", status_code=200)
def summarize_files_on_demand(
    summarization_request: SummarizationRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    query = summarization_request.query.to_query_parameters()
    task_scheduling_service.dispatch_summarize_files(
        query=query, system_prompt=summarization_request.system_prompt
    )
