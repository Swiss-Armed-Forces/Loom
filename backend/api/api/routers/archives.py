import logging
from typing import Annotated
from uuid import UUID

from bson import ObjectId
from common.archive.archive_repository import ArchiveRepository
from common.archive.archive_scheduling_service import ArchiveSchedulingService
from common.dependencies import (
    get_archive_repository,
    get_archive_scheduling_service,
    get_file_storage_service,
)
from common.services.file_storage_service import FileStorageService
from common.services.query_builder import QueryParameters
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.models.archives_model import ArchivesModel
from api.utils import get_content_disposition_header

router = APIRouter()

logger = logging.getLogger(__name__)

default_archive_repository = Depends(get_archive_repository)
default_archive_scheduling_service = Depends(get_archive_scheduling_service)
default_file_storage_service = Depends(get_file_storage_service)


class ArchiveCreatedResponse(BaseModel):
    """File id of the created archive."""

    archive_id: UUID


class ArchiveRequest(BaseModel):
    """Query to filter archives."""

    query: QueryParameters


class UpdateArchiveModel(BaseModel):
    """Update archive model."""

    hidden: bool


@router.get("/")
def get_all_archives(
    archive_repository: ArchiveRepository = default_archive_repository,
) -> ArchivesModel:
    """Get all archives."""
    all_archives = list(
        archive_repository.get_generator_by_query(
            QueryParameters(
                query_id=archive_repository.open_point_in_time(), search_string="*"
            )
        )
    )
    return ArchivesModel.from_archive_list(all_archives)


@router.post("/", status_code=201)
def create_new_archive(
    archive_request: ArchiveRequest,
    archive_scheduling_service: ArchiveSchedulingService = default_archive_scheduling_service,
) -> ArchiveCreatedResponse:
    """Create a new archive containing all files that match the query."""

    archive = archive_scheduling_service.create_archive(query=archive_request.query)

    return ArchiveCreatedResponse(archive_id=archive.id_)


class DownloadArchiveQuery(BaseModel):
    encrypted: bool = False


@router.get("/{archive_id}", status_code=200)
def download_archive(
    archive_id: UUID,
    query: Annotated[DownloadArchiveQuery, Query()],
    archive_repository: ArchiveRepository = default_archive_repository,
    file_storage_service: FileStorageService = default_file_storage_service,
) -> Response:
    """Download an archive by id."""
    archive = archive_repository.get_by_id(archive_id)
    if archive is None:
        raise HTTPException(status_code=404, detail="Invalid archive")
    archive_file = archive.plain_file if not query.encrypted else archive.encrypted_file
    archive_name = archive.name if not query.encrypted else archive.name_encrypted

    file_stream = file_storage_service.open_download_iterator(
        file_id=ObjectId(archive_file.storage_id)
    )
    return StreamingResponse(
        content=file_stream,
        media_type="archive/zip",
        headers={
            **get_content_disposition_header(archive_name),
        },
    )


@router.post("/{archive_id}")
def update_archive(
    archive_id: UUID,
    update_file_model: UpdateArchiveModel,
    archive_repository: ArchiveRepository = default_archive_repository,
):
    """Update archive."""
    archive = archive_repository.get_by_id(archive_id)
    if archive is None:
        raise HTTPException(status_code=404, detail="Invalid archive")
    archive.hidden = update_file_model.hidden
    archive_repository.update(archive, include={"hidden"})
