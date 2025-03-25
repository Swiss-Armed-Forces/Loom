"""Files router."""

import logging
from typing import Annotated, Any, Literal
from uuid import UUID

from bson import ObjectId
from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_lazybytes_service,
    get_task_scheduling_service,
)
from common.file.file_repository import (
    TREE_PATH_MAX_ELEMENT_COUNT,
    FileRepository,
    Stat,
)
from common.file.file_scheduling_service import FileSchedulingService
from common.models.es_repository import (
    InvalidSortFieldExceptions,
    PaginationParameters,
    SortingParameters,
)
from common.services.file_storage_service import FileStorageService
from common.services.lazybytes_service import LazyBytesService
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import TaskSchedulingService
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, RootModel

from api.models.query_model import QueryModel
from api.models.statistics_model import GenericStatisticsModel, SummaryStatisticsModel
from api.models.tree_model import TreeNodeModel
from api.utils import get_content_disposition_header

logger = logging.getLogger(__name__)
CONTENT_PREVIEW_LENGTH = 1000

DEFAULT_PAGE_SIZE = 10

SOURCE_ID = "api-upload"
router = APIRouter()

default_file_scheduling_service = Depends(get_file_scheduling_service)
default_file_repository = Depends(get_file_repository)
default_lazybytes_service = Depends(get_lazybytes_service)
default_file_storage_service = Depends(get_file_storage_service)
default_task_scheduling_service = Depends(get_task_scheduling_service)


class FileUploadResponse(BaseModel):
    """File id of the created archive."""

    file_id: UUID


@router.post("/")
def upload_file(
    file: UploadFile,
    file_scheduling_service: FileSchedulingService = default_file_scheduling_service,
    lazybytes_service: LazyBytesService = default_lazybytes_service,
) -> FileUploadResponse:
    """Upload new file that will be processed by Loom."""
    file_content = lazybytes_service.from_file(file.file)
    scheduled_file = file_scheduling_service.index_file(
        file.filename if file.filename is not None else "", file_content, SOURCE_ID
    )
    return FileUploadResponse(file_id=scheduled_file.id_)


class GetFilesFileEntry(BaseModel):
    file_id: UUID
    sort_field_value: str | None
    sort_id: list[Any] | None


class GetFilesResponse(BaseModel):
    files: list[GetFilesFileEntry]
    total_files: int
    sort_by_field: str


# pylint: disable=too-many-arguments
@router.get("/")
def get_files(
    sort_by_field: str = "_score",
    sort_direction: Literal["asc", "desc"] = "asc",
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    file_repository: FileRepository = default_file_repository,
    sort_id: Annotated[list[Any] | None, Query()] = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> GetFilesResponse:
    """Get list of file_id."""
    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("Getting files with query: '%s'", search_string)

    sorting_parameters = SortingParameters(
        field=sort_by_field, direction=sort_direction
    )

    pagination_parameters = PaginationParameters(sort_id=sort_id, size=page_size)
    try:
        result = list(
            file_repository.get_id_generator_by_query(
                query=query,
                sort_params=sorting_parameters,
                pagination_params=pagination_parameters,
            )
        )
        total_files = file_repository.count_by_query(query=query)
    except InvalidSortFieldExceptions as e:
        raise HTTPException(status_code=400, detail=str(e.args)) from e
    current_query_file_resp = GetFilesResponse(
        files=list(
            map(
                lambda get_files_file_entry: GetFilesFileEntry(
                    file_id=get_files_file_entry.id_,
                    sort_field_value=get_files_file_entry.sort_value,
                    sort_id=get_files_file_entry.sort,
                ),
                result,
            )
        ),
        total_files=total_files,
        sort_by_field=sort_by_field,
    )
    return current_query_file_resp


class UpdateFilesRequest(BaseModel):
    """Hides file model."""

    query: QueryModel
    hidden: bool


@router.put("/")
def update_files_by_query(
    update_files_model: UpdateFilesRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    """Update file."""
    query = update_files_model.query.to_query_parameters()
    task_scheduling_service.dispatch_set_hidden_state(query, update_files_model.hidden)


class GetFilesTreeResponse(RootModel):
    root: list[TreeNodeModel]


@router.get("/tree")
def get_files_tree(
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    node_path: str = "/",
    file_repository: FileRepository = default_file_repository,
) -> GetFilesTreeResponse:
    """Get a node out of the tree of files non-recursively."""

    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("Get file tree node with query: '%s'", query)

    tree_paths = file_repository.get_full_paths_by_query(
        query=query, tree_node_directory_path=node_path
    )
    return GetFilesTreeResponse(
        [TreeNodeModel.model_validate(node.model_dump()) for node in tree_paths]
    )


@router.get("/tree/max_element_count")
def get_tree_max_element_count() -> int:
    """Expose this constant for the frontend in case we need to change it."""

    return TREE_PATH_MAX_ELEMENT_COUNT


@router.get("/stats/summary")
def get_summary_stats(
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    file_repository: FileRepository = default_file_repository,
) -> SummaryStatisticsModel:
    """Get statistics about the files found by the provided query."""
    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("Get summary stats with query: '%s'", query)
    stats = file_repository.get_stat_summary(query)
    return SummaryStatisticsModel.from_statistics_summary(stats)


@router.get("/stats/generic/{stat_name}")
def get_generic_stats(
    stat_name: Stat,
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    file_repository: FileRepository = default_file_repository,
) -> GenericStatisticsModel:
    try:
        Stat(stat_name)
    except ValueError as e:
        raise HTTPException(422, f"Unknown stat '{stat_name}'") from e
    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("Get %s stats with query: '%s'", stat_name, query)
    stats = file_repository.get_stat_generic(query, stat=Stat(stat_name))
    return GenericStatisticsModel.from_statistics_generic(stats)


class UpdateFileRequest(BaseModel):
    """Update file model."""

    hidden: bool


@router.put("/{file_id}")
def update_file(
    file_id: UUID,
    update_file_request: UpdateFileRequest,
    file_repository: FileRepository = default_file_repository,
):
    """Update file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    file.hidden = update_file_request.hidden
    file_repository.update(file, include={"hidden"})


class GetFileLanguageTranslations(BaseModel):
    confidence: float
    language: str
    text: str


class GetFileResponse(BaseModel):
    file_id: UUID
    highlight: dict[str, list[str]] | None
    content: str
    name: str  # short_name
    libretranslate_language_translations: list[GetFileLanguageTranslations]
    raw: str
    summary: str | None


@router.get("/{file_id}")
def get_file(
    file_id: UUID,
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    file_repository: FileRepository = default_file_repository,
) -> GetFileResponse:
    """Get file data of file file_id."""
    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("Get file data of file with id %s", file_id)
    file = file_repository.get_by_id_with_query(
        id_=file_id, query=query, full_highlight_context=True
    )
    if file is None:
        raise HTTPException(status_code=404, detail="file not found")
    return GetFileResponse(
        file_id=file.id_,
        highlight=file.es_meta.highlight,
        content=str(file.content if file.content is not None else ""),
        name=str(file.short_name),
        libretranslate_language_translations=list(
            map(
                lambda libretranslate_translations: GetFileLanguageTranslations(
                    confidence=libretranslate_translations.confidence,
                    language=libretranslate_translations.language,
                    text=libretranslate_translations.text,
                ),
                file.libretranslate_translations,
            )
        ),
        raw=file.model_dump_json(
            exclude={"embeddings", "content", "libretranslate_translations"}
        ),
        summary=file.summary,
    )


class GetFilePreviewResponse(BaseModel):
    file_id: UUID
    tags: list[str] = []
    hidden: bool
    content: str
    content_preview_is_truncated: bool
    content_is_truncated: bool
    name: str  # short_name
    path: str  # full_path
    has_thumbnail: bool
    has_attachments: bool
    file_extension: str
    highlight: dict[str, list[str]] | None = {}
    tasks_succeeded: list[UUID] = []
    tasks_retried: list[UUID] = []
    tasks_failed: list[UUID] = []
    summary: str | None


@router.get("/{file_id}/preview")
def get_file_preview(
    file_id: UUID,
    search_string: str = "*",
    search_languages: Annotated[list[str] | None, Query()] = None,
    file_repository: FileRepository = default_file_repository,
) -> GetFilePreviewResponse:
    """Get preview data of file."""
    query = QueryParameters(search_string=search_string, languages=search_languages)
    logger.info("get file preview data of file with id %s", file_id)
    file = file_repository.get_by_id_with_query(
        id_=file_id, query=query, full_highlight_context=False
    )
    if file is None:
        raise HTTPException(status_code=404, detail="file not found")
    if file.content is None:
        file.content = ""
    return GetFilePreviewResponse(
        file_id=file.id_,
        tags=file.tags,
        hidden=file.hidden,
        content=str(file.content[:CONTENT_PREVIEW_LENGTH]),
        # Determine if the content preview of the file is truncated based on the file content
        # length and the content preview length
        content_preview_is_truncated=len(file.content) > CONTENT_PREVIEW_LENGTH,
        content_is_truncated=file.content_truncated,
        # Convert the file's short name to a string, or set it to an empty string if it is None
        name=str(file.short_name),
        path=str(file.full_path),
        has_thumbnail=bool(file.thumbnail_file_id),
        has_attachments=bool(file.has_attachments),
        file_extension=str(file.extension),
        highlight=file.es_meta.highlight,
        tasks_succeeded=file.tasks_succeeded,
        tasks_failed=file.tasks_failed,
        tasks_retried=file.tasks_retried,
        summary=file.summary,
    )


@router.get("/{file_id}/thumbnail")
def get_thumbnail(
    file_id: UUID,
    preview: bool = False,
    file_repository: FileRepository = default_file_repository,
    file_storage_service: FileStorageService = default_file_storage_service,
) -> Response:
    """Get thumbnail for the file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    file_stream = file_storage_service.open_download_iterator(
        file_id=ObjectId(
            file.thumbnail_file_id if not preview else file.preview_file_id
        )
    )
    return StreamingResponse(
        content=file_stream,
        headers={
            **get_content_disposition_header(file.thumbnail_file_id),
        },
    )


@router.post("/{file_id}/index", status_code=200)
def index_file(
    file_id: UUID,
    file_scheduling_service: FileSchedulingService = default_file_scheduling_service,
):
    """Re-index file."""
    file_scheduling_service.reindex_file(file_id)


class TranslateFileRequest(BaseModel):
    lang: str


@router.post("/{file_id}/translate", status_code=200)
def translate_file(
    file_id: UUID,
    translation_request: TranslateFileRequest,
    file_scheduling_service: FileSchedulingService = default_file_scheduling_service,
):
    file_scheduling_service.translate_file(
        file_id,
        translation_request.lang,
    )


class SummarizeFileRequest(BaseModel):
    system_prompt: str | None = None


@router.post("/{file_id}/summarize", status_code=200)
def summarize_file(
    file_id: UUID,
    summarize_request: SummarizeFileRequest,
    file_scheduling_service: FileSchedulingService = default_file_scheduling_service,
):
    """Summarize file."""
    file_scheduling_service.summarize_file(
        file_id=file_id, system_prompt=summarize_request.system_prompt
    )


@router.get("/{file_id}/download", status_code=200)
def download_file(
    file_id: UUID,
    file_repository: FileRepository = default_file_repository,
    file_storage_service: FileStorageService = default_file_storage_service,
) -> Response:
    """Download file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    file_stream = file_storage_service.open_download_iterator(
        file_id=ObjectId(file.storage_id)
    )
    return StreamingResponse(
        content=file_stream,
        headers={
            **get_content_disposition_header(file.short_name),
        },
    )


@router.get("/{file_id}/text", response_model=dict)
def download_text(
    file_id: UUID,
    file_repository: FileRepository = default_file_repository,
) -> Response:
    """Download content of file as text."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    return Response(
        content=str.encode(str(file.content)),
        headers={
            **get_content_disposition_header(file.short_name_content),
        },
    )


@router.post("/{file_id}/tags/{tag_to_add}")
def add_tag(
    file_id: UUID,
    tag_to_add: str,
    file_repository: FileRepository = default_file_repository,
):
    """Add tag to file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    try:
        # We deliberatly use += and not .append() here,
        # this is to trigger pydantic validation
        file.tags += [tag_to_add]
    except ValueError as ex:
        raise HTTPException(status_code=400, detail="Invalid tag") from ex
    file_repository.update(file, include={"tags"})


@router.delete("/{file_id}/tags/{tag_to_remove}")
def delete_tag(
    file_id: UUID,
    tag_to_remove: str,
    file_repository: FileRepository = default_file_repository,
):
    """Delete tag from file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    try:
        file.tags.remove(tag_to_remove)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail="Tag to remove not found") from ex
    file_repository.update(file, include={"tags"})
