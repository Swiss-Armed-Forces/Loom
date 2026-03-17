import logging

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_task_scheduling_service,
)
from common.file.file_repository import FileRepository, Tag
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)


router = APIRouter()

default_file_scheduling_service = Depends(get_file_scheduling_service)
default_file_repository = Depends(get_file_repository)
default_task_scheduling_service = Depends(get_task_scheduling_service)


AllTags = list[str]


class AddTagsByQueryRequest(BaseModel):
    tags: list[Tag]
    query: QueryParameters


@router.get("/")
def get_tags(file_repository: FileRepository = default_file_repository) -> AllTags:
    return file_repository.get_all_tags()


@router.post("/", status_code=200)
def add_tags(
    tags_to_add_request: AddTagsByQueryRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_add_tags_to_files(
        query=tags_to_add_request.query, tags=tags_to_add_request.tags
    )


@router.delete("/{tag_to_delete}", status_code=200)
def delete_tag(
    tag_to_delete: str,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_remove_tag(tag=tag_to_delete)
