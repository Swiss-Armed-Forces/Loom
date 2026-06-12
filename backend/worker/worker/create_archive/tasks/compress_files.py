import datetime
import logging
from pathlib import Path
from textwrap import dedent
from typing import cast
from uuid import UUID

from common.archive.archive_repository import Archive
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import (
    FileStorageLazyBytes,
    LazyBytes,
    TempTypedLazyBytes,
)
from pydantic import BaseModel
from stream_zip import ZIP_32, stream_zip

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks.archive_format import (
    CLI_DOC,
    CLI_FILENAME,
    FILES_DIR,
    FILES_INDEX_DIR,
    JSON_INDENT,
    JSON_SUFFIX,
    MANIFEST_FILENAME,
    README_FILENAME,
    ZIP_EXTENSION,
    build_parser,
)
from worker.create_archive.tasks.query_file_list import FileIdList

logger = logging.getLogger(__name__)

app = get_celery_app()


def _readme_content(archive_name: str) -> bytes:
    lbl_manifest = f"- `{MANIFEST_FILENAME}`"
    lbl_cli = f"- `{CLI_FILENAME}`"
    lbl_files = f"- `{FILES_DIR}/`"
    lbl_index = f"- `{FILES_INDEX_DIR}/`"
    col = max(len(lbl_manifest), len(lbl_cli), len(lbl_files), len(lbl_index))
    cli_help = build_parser().format_help()
    header = dedent(f"""\
        # Loom Archive — {archive_name}

        This archive was created by Loom.

        ## Structure

        {lbl_manifest:<{col}} — archive metadata and query parameters (JSON)
        {lbl_cli:<{col}} — interactive CLI for browsing and extracting files
        {lbl_files:<{col}} — raw file bytes, keyed by storage UUID
        {lbl_index:<{col}} — fully-indexed file metadata (JSON, one file per entry)

        Each `{FILES_INDEX_DIR}/{{id}}{JSON_SUFFIX}` holds the indexed metadata for one file.
        Raw bytes (if available) are stored at `{FILES_DIR}/{{uuid}}`.

        """)
    return (
        header
        + CLI_DOC.strip()
        + "\n\n### Command reference\n\n```\n"
        + cli_help
        + "```\n"
    ).encode()


def _collect_lazybytes(model: BaseModel) -> list[FileStorageLazyBytes]:
    """Recursively collect all LazyBytes instances from a Pydantic model's fields."""
    result: list[FileStorageLazyBytes] = []
    for field_name in type(model).model_fields:
        value = getattr(model, field_name)
        if isinstance(value, LazyBytes):
            result.append(cast(FileStorageLazyBytes, value))
        elif isinstance(value, BaseModel):
            result.extend(_collect_lazybytes(value))
    return result


def _file_storage_fields(file: File) -> list[FileStorageLazyBytes]:
    """Return all FileStorageLazyBytes with a service_id for the given file."""
    return [s for s in _collect_lazybytes(file) if s.service_id is not None]


def _cli_content() -> bytes:
    return (Path(__file__).parent / "archive_format.py").read_bytes()


def _manifest_content(archive: Archive) -> bytes:
    return archive.model_dump_json(indent=JSON_INDENT).encode()


def _file_archive_entries(
    file_id: UUID,
    archive_id: UUID,
    archive_name: str,
    modified_at: datetime.datetime,
    perms: int,
):
    """Yield ZIP entries for a single file, re-querying it from the repository for fresh
    metadata."""
    fresh_file = get_file_repository().get_by_id(file_id)
    if fresh_file is None:
        logger.warning(
            "Skipping file '%s' from archive: not found in repository", file_id
        )
        return
    if fresh_file.storage_data is None:
        logger.warning(
            "Skipping file '%s' from archive: no storage data", fresh_file.full_path
        )
        return

    # Inject the archive link in-memory — the async persist_file_to_archive_link tasks
    # may not have flushed to ES yet, so we ensure the serialized file is up-to-date.
    if str(archive_id) not in fresh_file.archives:
        fresh_file.archives = fresh_file.archives + [str(archive_id)]

    file_storage_service = get_file_storage_service()
    for storage in _file_storage_fields(fresh_file):
        yield (
            f"{archive_name}/{FILES_DIR}/{storage.service_id}",
            modified_at,
            perms,
            ZIP_32,
            file_storage_service.load_generator(storage),
        )

    file_json = fresh_file.model_dump_json(indent=JSON_INDENT).encode()
    yield (
        f"{archive_name}/{FILES_INDEX_DIR}/{fresh_file.id_}{JSON_SUFFIX}",
        modified_at,
        perms,
        ZIP_32,
        iter([file_json]),
    )


def _archive_data(file_ids: list[UUID], archive: Archive):
    archive_name = archive.name.removesuffix(ZIP_EXTENSION)
    modified_at = datetime.datetime.now()
    perms = 0o600

    manifest = _manifest_content(archive)
    yield (
        f"{archive_name}/{MANIFEST_FILENAME}",
        modified_at,
        0o644,
        ZIP_32,
        iter([manifest]),
    )

    readme = _readme_content(archive_name)
    yield (
        f"{archive_name}/{README_FILENAME}",
        modified_at,
        0o644,
        ZIP_32,
        iter([readme]),
    )

    cli = _cli_content()
    yield (
        f"{archive_name}/{CLI_FILENAME}",
        modified_at,
        0o755,
        ZIP_32,
        iter([cli]),
    )

    for file_id in file_ids:
        yield from _file_archive_entries(
            file_id, archive.id_, archive_name, modified_at, perms
        )


def stream_archive(file_ids: list[UUID], archive: Archive):
    """Return a stream_zip generator for the given archive."""
    return stream_zip(_archive_data(file_ids, archive))


@app.task(
    base=ArchiveProcessingTask,
)
def compress_files_task(
    lazy_file_ids: TempTypedLazyBytes[FileIdList], archive: Archive
) -> FileStorageLazyBytes:
    """Load files from storage and compress them.

    :param lazy_file_ids: Lazybytes handle to the list of file IDs to compress
    :return: the destination file
    """
    file_ids = get_lazybytes_service().load_object(lazy_file_ids)
    file_storage_service = get_file_storage_service()

    zipped_chunks = stream_archive(file_ids, archive)

    compressed_file_storage_data = file_storage_service.from_generator(
        iter(zipped_chunks)
    )
    return compressed_file_storage_data
