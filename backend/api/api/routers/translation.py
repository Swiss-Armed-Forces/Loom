"""Translation router."""

import logging
from urllib.error import URLError

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_libretranslate_api,
    get_task_scheduling_service,
)
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.settings import settings

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


class LibretranslateSupportedLanguages(BaseModel):
    code: str
    name: str


@router.get("/languages", status_code=200)
def get_supported_languages() -> list[LibretranslateSupportedLanguages]:
    api = get_libretranslate_api()
    try:
        languages = [
            LibretranslateSupportedLanguages(**lang)
            for lang in api.languages(timeout=LIBRETRANSLATE_REQUEST_TIMEOUT)
        ]
    except URLError as exc:
        logger.warning("Exception getting supported languages", exc_info=exc)
        return []
    return [lang for lang in languages if lang.code != settings.translate_target]


@router.post("/", status_code=200)
def translate_files_on_demand(
    translation_request: TranslateAllRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_translate_files(
        query=translation_request.query,
        lang=translation_request.lang,
    )
