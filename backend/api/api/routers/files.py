import logging
from typing import Annotated, Any, List, Literal
from uuid import UUID

from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_lazybytes_service,
    get_task_scheduling_service,
)
from common.file.file_repository import (
    TREE_PATH_MAX_ELEMENT_COUNT,
    Attachment,
    File,
    FileNotFoundException,
    FileRepository,
    ImapInfo,
    Stat,
    Tag,
)
from common.file.file_scheduling_service import FileSchedulingService
from common.models.es_repository import (
    InvalidSortFieldExceptions,
    PaginationParameters,
    SortingParameters,
)
from common.services.lazybytes_service import LazyBytes, LazyBytesService
from common.services.query_builder import (
    DEFAULT_PIT_KEEPALIVE,
    KeepAlive,
    QueryParameters,
)
from common.services.task_scheduling_service import (
    TaskSchedulingService,
    UpdateFileRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, RootModel

from api.models.statistics_model import GenericStatisticsModel, SummaryStatisticsModel
from api.models.tree_model import TreeNodeModel
from api.utils import get_content_disposition_header

logger = logging.getLogger(__name__)
CONTENT_PREVIEW_LENGTH = 1000
MAX_ATTACHMENTS_PREVIEW = 20


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
        full_name=file.filename if file.filename is not None else "",
        file_content=file_content,
        source_id=SOURCE_ID,
        parent_id=None,
    )
    return FileUploadResponse(file_id=scheduled_file.id_)


class GetQueryResponse(BaseModel):
    query_id: str
    keep_alive: KeepAlive


class GetQuery(BaseModel):
    keep_alive: KeepAlive = DEFAULT_PIT_KEEPALIVE


@router.post("/query")
def get_query(
    query: Annotated[GetQuery, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetQueryResponse:
    query_id = file_repository.open_point_in_time(keep_alive=query.keep_alive)
    return GetQueryResponse(query_id=query_id, keep_alive=query.keep_alive)


class GetFilesFileEntry(BaseModel):
    file_id: UUID
    sort_field_value: str | None
    sort_id: list[Any] | None


class GetFilesResponse(BaseModel):
    files: list[GetFilesFileEntry]
    sort_by_field: str


class GetFilesQuery(QueryParameters, SortingParameters, PaginationParameters):
    pass


@router.get("/")
def get_files(
    query: Annotated[GetFilesQuery, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetFilesResponse:
    """Get files for a given query."""
    logger.info("Getting files with query: '%s'", query)
    try:
        result = list(
            file_repository.get_id_generator_by_query(
                query=query,
                sort_params=query,
                pagination_params=query,
            )
        )
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
        sort_by_field=query.sort_by_field,
    )
    return current_query_file_resp


class UpdateFilesRequest(BaseModel):
    query: QueryParameters
    request: UpdateFileRequest


@router.put("/")
def update_files_by_query(
    update_files_model: UpdateFilesRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_update(
        query=update_files_model.query, request=update_files_model.request
    )


class GetFilesCountResponse(BaseModel):
    total_files: int


@router.get("/count")
def get_files_count(
    query: Annotated[QueryParameters, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetFilesCountResponse:
    """Get files for a given query."""
    logger.info("Getting files with query: '%s'", query)
    total_files = file_repository.count_by_query(query=query)
    return GetFilesCountResponse(total_files=total_files)


class GetFilesTreeResponse(RootModel):
    root: list[TreeNodeModel]


class GetFilesTreeQuery(QueryParameters):
    node_path: str = "/"


@router.get("/tree")
def get_files_tree(
    query: Annotated[GetFilesTreeQuery, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetFilesTreeResponse:
    """Get a node out of the tree of files non-recursively."""

    logger.info("Get file tree node with query: '%s'", query)

    tree_paths = file_repository.get_full_paths_by_query(
        query=query, tree_node_directory_path=query.node_path
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
    query: Annotated[QueryParameters, Query()],
    file_repository: FileRepository = default_file_repository,
) -> SummaryStatisticsModel:
    """Get statistics about the files found by the provided query."""
    logger.info("Get summary stats with query: '%s'", query)
    stats = file_repository.get_stat_summary(query=query)
    return SummaryStatisticsModel.from_statistics_summary(stats)


@router.get("/stats/generic/{stat}")
def get_generic_stats(
    stat: Stat,
    query: Annotated[QueryParameters, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GenericStatisticsModel:
    logger.info("Get %s stats with query: '%s'", stat, query)
    stats = file_repository.get_stat_generic(query=query, stat=stat)
    return GenericStatisticsModel.from_statistics_generic(stats)


@router.put("/{file_id}")
def update_file(
    file_id: UUID,
    update_file_request: UpdateFileRequest,
    file_scheduling_service: FileSchedulingService = default_file_scheduling_service,
):
    try:
        file_scheduling_service.update_file(file_id, update_file_request)
    except FileNotFoundException as e:
        raise HTTPException(status_code=404, detail="Invalid file") from e


class GetFileLanguageTranslations(BaseModel):
    confidence: float
    language: str
    text: str


class RenderedFile(BaseModel):
    image_file_id: str | None = None
    office_pdf_file_id: str | None = None
    browser_pdf_file_id: str | None = None


class GetFileResponse(BaseModel):
    file_id: UUID
    highlight: dict[str, list[str]] | None
    content: str
    name: str
    full_path: str
    libretranslate_language_translations: list[GetFileLanguageTranslations]
    raw: str
    summary: str | None
    type: str | None
    imap: ImapInfo | None
    rendered_file: RenderedFile

    @staticmethod
    def from_file(file: File):
        return GetFileResponse(
            file_id=file.id_,
            highlight=file.es_meta.highlight,
            content=str(file.content if file.content is not None else ""),
            name=str(file.short_name),
            full_path=str(file.full_path),
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
                exclude={
                    "embeddings",
                    "content",
                    "libretranslate_translations",
                    "attachments",
                },
                exclude_none=True,
                exclude_unset=True,
            ),
            summary=file.summary,
            type=file.magic_file_type,
            imap=file.imap,
            rendered_file=RenderedFile(
                image_file_id=service_id(file.rendered_file.image_data),
                browser_pdf_file_id=service_id(file.rendered_file.browser_pdf_data),
                office_pdf_file_id=service_id(file.rendered_file.office_pdf_data),
            ),
        )


def service_id(lb: LazyBytes | None) -> str | None:
    if not lb:
        return None
    return lb.service_id


@router.get("/{file_id}")
def get_file(
    file_id: UUID,
    query: Annotated[QueryParameters, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetFileResponse:
    """Get file data of file file_id."""
    logger.info("Get file data of file with id %s", file_id)
    file = file_repository.get_by_id_with_query(
        id_=file_id, query=query, full_highlight_context=True
    )
    if file is None:
        raise HTTPException(status_code=404, detail="file not found")
    return GetFileResponse.from_file(file)


class GetFilePreviewResponse(BaseModel):
    file_id: UUID
    parent_id: UUID | None
    tags: list[Tag] = []
    flagged: bool
    hidden: bool
    content: str
    content_preview_is_truncated: bool
    content_is_truncated: bool
    name: str  # short_name
    path: str  # full_path
    thumbnail_file_id: str | None
    thumbnail_total_frames: int | None
    attachments: list[Attachment] = []
    attachments_total_count: int = 0
    file_extension: str
    highlight: dict[str, list[str]] | None = {}
    tasks_succeeded: list[UUID] = []
    tasks_retried: list[UUID] = []
    tasks_failed: list[UUID] = []
    summary: str | None
    is_spam: bool | None = False


@router.get("/{file_id}/preview")
def get_file_preview(
    file_id: UUID,
    query: Annotated[QueryParameters, Query()],
    file_repository: FileRepository = default_file_repository,
) -> GetFilePreviewResponse:
    """Get preview data of file."""
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
        parent_id=file.parent_id,
        tags=file.tags,
        flagged=file.flagged,
        hidden=file.hidden,
        content=str(file.content[:CONTENT_PREVIEW_LENGTH]),
        # Determine if the content preview of the file is truncated based on the file content
        # length and the content preview length
        content_preview_is_truncated=len(file.content) > CONTENT_PREVIEW_LENGTH,
        content_is_truncated=file.content_truncated,
        # Convert the file's short name to a string, or set it to an empty string if it is None
        name=str(file.short_name),
        path=str(file.full_path),
        thumbnail_file_id=service_id(file.thumbnail_data),
        thumbnail_total_frames=file.thumbnail_total_frames,
        attachments=file.attachments[:MAX_ATTACHMENTS_PREVIEW],
        attachments_total_count=len(file.attachments),
        file_extension=str(file.extension),
        highlight=file.es_meta.highlight,
        tasks_succeeded=file.tasks_succeeded,
        tasks_failed=file.tasks_failed,
        tasks_retried=file.tasks_retried,
        summary=file.summary,
        is_spam=file.is_spam,
    )


@router.get("/{file_id}/thumbnail/{thumbnail_file_id}")
def get_thumbnail(
    file_id: UUID,
    thumbnail_file_id: str,
    file_repository: FileRepository = default_file_repository,
    file_storage_service: LazyBytesService = default_file_storage_service,
) -> Response:
    """Get thumbnail of a file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")

    file_stream = file_storage_service.load_generator(
        LazyBytes(service_id=thumbnail_file_id)
    )
    return StreamingResponse(
        content=file_stream,
        headers={
            **get_content_disposition_header(
                "inline", f"{file.short_name}.thumbnail.png"
            ),
        },
    )


@router.get("/{file_id}/rendered/{rendered_id}")
def get_rendered(
    file_id: UUID,
    rendered_id: str,
    file_repository: FileRepository = default_file_repository,
    file_storage_service: LazyBytesService = default_file_storage_service,
) -> Response:
    """Get rendered version of a file."""
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")

    file_stream = file_storage_service.load_generator(LazyBytes(service_id=rendered_id))
    return StreamingResponse(
        content=file_stream,
        headers={
            **get_content_disposition_header("inline", f"{file.short_name}.rendered"),
        },
    )


@router.post("/{file_id}/index", status_code=200)
def index_file(
    file_id: UUID,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_reindex_file(file_id=file_id)


class TranslateFileRequest(BaseModel):
    lang: str


@router.post("/{file_id}/translate", status_code=200)
def translate_file(
    file_id: UUID,
    translation_request: TranslateFileRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_translate_file(
        file_id=file_id,
        lang=translation_request.lang,
    )


class SummarizeFileRequest(BaseModel):
    system_prompt: str | None = None


@router.post("/{file_id}/summarize", status_code=200)
def summarize_file(
    file_id: UUID,
    summarize_request: SummarizeFileRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_summarize_file(
        file_id=file_id, system_prompt=summarize_request.system_prompt
    )


@router.get("/{file_id}/download", status_code=200)
def download_file(
    file_id: UUID,
    content_disposition: Literal["inline", "attachment"] = "attachment",
    file_repository: FileRepository = default_file_repository,
    file_storage_service: LazyBytesService = default_file_storage_service,
) -> Response:
    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="Invalid file")
    if file.storage_data is None:
        raise HTTPException(status_code=404, detail="File content not available")
    file_stream = file_storage_service.load_generator(file.storage_data)
    return StreamingResponse(
        content=file_stream,
        headers={
            **get_content_disposition_header(content_disposition, file.short_name),
        },
    )


class AddTagsRequest(BaseModel):
    tags: List[Tag]


@router.post("/{file_id}/tags")
def add_tags(
    file_id: UUID,
    request: AddTagsRequest,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_add_tags_to_file(
        file_id=file_id, tags=request.tags
    )


@router.delete("/{file_id}/tags/{tag_to_remove}")
def delete_tag(
    file_id: UUID,
    tag_to_remove: Tag,
    task_scheduling_service: TaskSchedulingService = default_task_scheduling_service,
):
    task_scheduling_service.dispatch_remove_tag_from_file(
        file_id=file_id, tag=tag_to_remove
    )
