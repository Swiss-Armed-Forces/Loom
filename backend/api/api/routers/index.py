import logging

from common.dependencies import get_file_repository, get_task_scheduling_service
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import (
    MAX_ADDITIONAL_RECURSION_DEPTH,
    IndexingPriority,
    TaskSchedulingService,
)
from common.settings import settings
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_task_scheduling_service = Depends(get_task_scheduling_service)


class IndexAllRequest(BaseModel):
    """Query to filter files."""

    query: QueryParameters
    additional_recursion_depth: int = Field(
        default=settings.indexing_max_recursion_depth,
        ge=0,
        le=MAX_ADDITIONAL_RECURSION_DEPTH,
        description="Levels of attachments to extract below each matched file,"
        " relative to that file's own recursion depth. 0 re-indexes the matched files"
        " alone. Defaults to the deployment's configured"
        " indexing_max_recursion_depth.",
    )


@router.post("", status_code=202)
def index_files_on_demand(
    index_request: IndexAllRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    # A sweep over a whole result set must not outrank the single-file re-index
    # someone is waiting on, so it stays in the normal band.
    task_scheduling_service.dispatch_reindex_files(
        query=index_request.query,
        additional_recursion_depth=index_request.additional_recursion_depth,
        priority=IndexingPriority.MEDIUM,
    )
