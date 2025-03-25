from uuid import UUID

from common.archive.archive_repository import Archive
from pydantic import BaseModel

from api.models.query_model import QueryModel


class ArchiveMeta(BaseModel):
    short_name: str
    query: QueryModel
    updated_datetime: str

    @staticmethod
    def from_archive(archive: Archive):
        return ArchiveMeta(
            short_name=archive.name,
            query=QueryModel.from_query_parameters(archive.query),
            updated_datetime=archive.created_at.isoformat(timespec="milliseconds"),
        )


class ArchiveContent(BaseModel):
    state: str
    size: int

    @staticmethod
    def from_archive(archive: Archive):
        return ArchiveContent(
            state=archive.state,
            size=archive.plain_file.size if archive.plain_file.size is not None else 0,
        )


class ArchiveHit(BaseModel):
    meta: ArchiveMeta
    content: ArchiveContent
    sha256: str | None
    sha256_encrypted: str | None
    hidden: bool
    file_id: UUID

    @staticmethod
    def from_archive(archive: Archive):
        return ArchiveHit(
            meta=ArchiveMeta.from_archive(archive),
            content=ArchiveContent.from_archive(archive),
            sha256=archive.plain_file.sha256 if archive.plain_file else None,
            sha256_encrypted=(
                archive.encrypted_file.sha256 if archive.encrypted_file else None
            ),
            hidden=False,
            file_id=archive.id_,
        )


class ArchivesModel(BaseModel):
    # similar to: HitsModel
    # pylint: disable=duplicate-code

    clean: bool
    hits: list[ArchiveHit]
    total: int
    found: int
    hasMore: bool
    currentPage: int

    @staticmethod
    def from_archive_list(archive_list: list[Archive]):
        return ArchivesModel(
            clean=False,
            hits=list(map(ArchiveHit.from_archive, archive_list)),
            total=len(archive_list),
            found=len(archive_list),
            hasMore=False,
            currentPage=0,
        )
