import io
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from common.archive.archive_repository import Archive
from common.dependencies import get_file_repository
from common.file.file_repository import File, FilePurePath
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    LazyBytes,
)
from common.services.query_builder import QueryParameters

from worker.create_archive.tasks.archive_format import ZIP_EXTENSION
from worker.create_archive.tasks.compress_files import stream_archive

_FIXED_DATETIME = datetime(2026, 6, 7, 9, 14, 40, 812597)


@dataclass
class ArchiveEntry:
    file: File
    content: bytes


def make_archive() -> Archive:
    return Archive(
        query=QueryParameters(search_string="*", query_id=str(uuid4())),
        created_at=_FIXED_DATETIME,
    )


def simple_entries(files: dict[str, bytes]) -> list[ArchiveEntry]:
    return [
        ArchiveEntry(
            file=File(
                full_name=FilePurePath(full_name),
                source="test",
                sha256="abc",
                size=len(content),
                storage_data=LazyBytes(service_id=uuid4()),
            ),
            content=content,
        )
        for full_name, content in files.items()
    ]


def build_archive_bytes(
    entries: list[ArchiveEntry],
    file_storage_service: InMemoryFileStorageLazyBytesService,
    archive: Archive | None = None,
) -> bytes:
    """Build a loom archive ZIP using the real stream_archive pipeline.

    Stores all entry content in file_storage_service so stream_archive can read it, then
    returns the raw ZIP bytes.
    """
    if archive is None:
        archive = make_archive()

    file_id_map = {e.file.id_: e.file for e in entries}
    get_file_repository().get_by_id.side_effect = file_id_map.get  # type: ignore[attr-defined]

    for entry in entries:
        f = entry.file
        for lb in [
            f.storage_data,
            f.thumbnail_data,
            f.rendered_file.image_data,
            f.rendered_file.office_pdf_data,
            f.rendered_file.browser_pdf_data,
        ]:
            if lb is not None and lb.service_id is not None:
                file_storage_service.from_file_with_id(
                    io.BytesIO(entry.content), lb.service_id
                )

    return b"".join(stream_archive([e.file.id_ for e in entries], archive))


def build_archive(
    tmp_path: Path,
    entries: list[ArchiveEntry],
    file_storage_service: InMemoryFileStorageLazyBytesService,
    archive: Archive | None = None,
) -> Path:
    """Build a loom archive and extract it to tmp_path.

    Returns the path to the extracted archive directory.
    """
    if archive is None:
        archive = make_archive()

    zip_bytes = build_archive_bytes(entries, file_storage_service, archive)
    archive_name = archive.name.removesuffix(ZIP_EXTENSION)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(tmp_path)

    return tmp_path / archive_name
