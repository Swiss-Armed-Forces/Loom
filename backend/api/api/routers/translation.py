"""Translation router."""

import logging

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_task_scheduling_service,
)
from common.file.file_repository import (
    LIBRETRANSLATE_SUPPORTED_LANGUAGES,
    LibretranslateSupportedLanguages,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_file_scheduling_service = Depends(get_file_scheduling_service)
default_task_scheduling_service = Depends(get_task_scheduling_service)

LIBRETRANSLATE_REQUEST_TIMEOUT = 5


class TranslateAllRequest(BaseModel):
    """Query to filter files."""

    lang: str
    query: QueryParameters


@router.get("/languages", status_code=200)
def get_supported_languages() -> list[LibretranslateSupportedLanguages]:
    return LIBRETRANSLATE_SUPPORTED_LANGUAGES


@router.post("/", status_code=200)
def translate_files_on_demand(
    translation_request: TranslateAllRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_translate_files(
        query=translation_request.query,
        lang=translation_request.lang,
    )
