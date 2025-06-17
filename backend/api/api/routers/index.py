import logging

from common.dependencies import get_file_repository, get_task_scheduling_service
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_task_scheduling_service = Depends(get_task_scheduling_service)


class IndexAllRequest(BaseModel):
    """Query to filter files."""

    query: QueryParameters


@router.post("/", status_code=200)
def index_files_on_demand(
    index_request: IndexAllRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_reindex_files(query=index_request.query)
