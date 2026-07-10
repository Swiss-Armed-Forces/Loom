import logging
import tempfile
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import NamedTuple, cast
from uuid import UUID

from common.archive.archive_repository import Archive
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import File, RenderedFile
from common.services.lazybytes_service import (
    FileStorageLazyBytes,
    LazyBytes,
    TempTypedLazyBytes,
)
from common.utils.pydantic_field_paths import iter_field_paths_by_type
from pydantic import BaseModel
from stream_zip import ZIP_64, MemberFile, stream_zip

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks.archive_cli import (
    CLI_DOC,
    CLI_ENTRYPOINT_FILENAME,
    CLI_FILENAME,
    FILES_DIR,
    FILES_INDEX_DIR,
    JSON_INDENT,
    JSON_SUFFIX,
    MANIFEST_FILENAME,
    README_FILENAME,
    SHELL_INDEX_FILENAME,
    ZIP_EXTENSION,
    build_parser,
)
from worker.create_archive.tasks.archive_cli._db import ShellIndexCollector
from worker.create_archive.tasks.archive_cli._types import StorageEntry
from worker.create_archive.tasks.query_file_list import FileIdList

logger = logging.getLogger(__name__)

app = get_celery_app()

_PERMS_FILE = 0o600
_PERMS_META = 0o644
_PERMS_EXEC = 0o755
_PROGRESS_LOG_INTERVAL_PCT = 5


def _readme_content(archive_name: str) -> bytes:
    lbl_entrypoint = f"- `{CLI_ENTRYPOINT_FILENAME}`"
    lbl_manifest = f"- `{MANIFEST_FILENAME}`"
    lbl_cli = f"- `{CLI_FILENAME}/`"
    lbl_files = f"- `{FILES_DIR}/`"
    lbl_index = f"- `{FILES_INDEX_DIR}/`"
    lbl_shell_index = f"- `{SHELL_INDEX_FILENAME}`"
    col = max(
        len(lbl_entrypoint),
        len(lbl_manifest),
        len(lbl_cli),
        len(lbl_files),
        len(lbl_index),
        len(lbl_shell_index),
    )
    cli_help = build_parser().format_help()
    header = dedent(f"""\
        # Loom Archive — {archive_name}

        This archive was created by Loom.

        ## Structure

        {lbl_entrypoint:<{col}} — entry point: run directly (`./cli.py`) or via `python cli.py`
        {lbl_manifest:<{col}} — archive metadata and query parameters (JSON)
        {lbl_cli:<{col}} — CLI package (required by `{CLI_ENTRYPOINT_FILENAME}`)
        {lbl_files:<{col}} — raw file bytes, keyed by storage UUID
        {lbl_index:<{col}} — fully-indexed file metadata (JSON, one file per entry)
        {lbl_shell_index:<{col}} — navigation index for the interactive shell (SQLite)

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


def _cli_entrypoint() -> bytes:
    """Return the bytes of cli.py, the top-level archive entry point."""
    return (Path(__file__).parent / CLI_FILENAME / CLI_ENTRYPOINT_FILENAME).read_bytes()


class _CliEntry(NamedTuple):
    filename: str
    content: bytes


def _cli_entries() -> list[_CliEntry]:
    """Return (filename, bytes) pairs for every package .py file in archive_cli.

    Excludes cli.py, which is embedded separately at the archive root.
    """
    pkg_dir = Path(__file__).parent / CLI_FILENAME
    return [
        _CliEntry(f.name, f.read_bytes())
        for f in sorted(pkg_dir.glob("*.py"))
        if f.name != CLI_ENTRYPOINT_FILENAME
    ]


def _manifest_content(archive: Archive) -> bytes:
    return archive.model_dump_json(indent=JSON_INDENT).encode()


def _fetch_file(file_id: UUID, archive_id: UUID) -> File | None:
    """Fetch a single File from ES."""
    file_ = get_file_repository().get_by_id(file_id)
    if file_ is None:
        logger.warning(
            "Skipping file '%s' from archive: not found in repository", file_id
        )
        return None
    if file_.storage_data is None:
        logger.warning(
            "Skipping file '%s' from archive: no storage data", file_.full_path
        )
        return None
    # Inject the archive link in-memory — the async persist_file_to_archive_link tasks
    # may not have flushed to ES yet, so we ensure the serialized file is up-to-date.
    if str(archive_id) not in file_.archives:
        file_.archives = file_.archives + [str(archive_id)]
    return file_


def _collect_storage_ids(file_: File) -> list[StorageEntry]:
    """Return StorageEntry list for all storage objects on the given file."""
    result: list[StorageEntry] = []
    if file_.storage_data is not None and file_.storage_data.service_id is not None:
        result.append(StorageEntry(str(file_.storage_data.service_id), "file"))
    if file_.thumbnail_data is not None and file_.thumbnail_data.service_id is not None:
        result.append(StorageEntry(str(file_.thumbnail_data.service_id), "thumbnail"))
    for field_path in iter_field_paths_by_type(RenderedFile, FileStorageLazyBytes):
        val = getattr(file_.rendered_file, field_path)
        if val is not None and val.service_id is not None:
            result.append(StorageEntry(str(val.service_id), f"rendered:{field_path}"))
    return result


def _file_archive_entries(
    file_ids: list[UUID],
    archive_id: UUID,
    archive_name: str,
    modified_at: datetime,
    collector: ShellIndexCollector,
) -> Iterator[MemberFile]:
    """Yield ZIP entries for all files."""
    file_storage_service = get_file_storage_service()
    total = len(file_ids)
    last_logged_pct = -1
    for index, file_id in enumerate(file_ids):
        pct = (index * 100) // total if total else 100
        if (
            pct // _PROGRESS_LOG_INTERVAL_PCT
            > last_logged_pct // _PROGRESS_LOG_INTERVAL_PCT
        ):
            last_logged_pct = pct
            logger.info("Compressing archive: %d/%d files (%d%%)", index, total, pct)
        file_ = _fetch_file(file_id, archive_id)
        if file_ is None:
            continue
        json_filename = f"{file_.id_}{JSON_SUFFIX}"
        collector.add_file(
            str(file_.full_path).lstrip("/"),
            str(file_.id_),
            json_filename,
            _collect_storage_ids(file_),
        )
        for storage in _file_storage_fields(file_):
            if not file_storage_service.exists(storage):
                logger.warning(
                    "Skipping storage object '%s' for file '%s': not found in file storage",
                    storage.service_id,
                    file_.full_path,
                )
                continue
            yield (
                f"{archive_name}/{FILES_DIR}/{storage.service_id}",
                modified_at,
                _PERMS_FILE,
                ZIP_64,
                file_storage_service.load_generator(storage),
            )
        file_json = file_.model_dump_json(indent=JSON_INDENT).encode()
        yield (
            f"{archive_name}/{FILES_INDEX_DIR}/{json_filename}",
            modified_at,
            _PERMS_FILE,
            ZIP_64,
            iter([file_json]),
        )
    logger.info("Compressing archive: %d/%d files (100%%)", total, total)


def _archive_data(file_ids: list[UUID], archive: Archive) -> Iterator[MemberFile]:
    archive_name = archive.name.removesuffix(ZIP_EXTENSION)
    modified_at = datetime.now()

    manifest = _manifest_content(archive)
    yield (
        f"{archive_name}/{MANIFEST_FILENAME}",
        modified_at,
        _PERMS_META,
        ZIP_64,
        iter([manifest]),
    )

    readme = _readme_content(archive_name)
    yield (
        f"{archive_name}/{README_FILENAME}",
        modified_at,
        _PERMS_META,
        ZIP_64,
        iter([readme]),
    )

    yield (
        f"{archive_name}/{CLI_ENTRYPOINT_FILENAME}",
        modified_at,
        _PERMS_EXEC,
        ZIP_64,
        iter([_cli_entrypoint()]),
    )

    for entry in _cli_entries():
        yield (
            f"{archive_name}/{CLI_FILENAME}/{entry.filename}",
            modified_at,
            _PERMS_META,
            ZIP_64,
            iter([entry.content]),
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        collector = ShellIndexCollector(Path(tmpdir) / SHELL_INDEX_FILENAME)
        yield from _file_archive_entries(
            file_ids, archive.id_, archive_name, modified_at, collector
        )

        # collector is now fully populated — yield the navigation index streamed from disk
        yield (
            f"{archive_name}/{SHELL_INDEX_FILENAME}",
            modified_at,
            _PERMS_META,
            ZIP_64,
            collector.stream_db(),
        )


def stream_archive(file_ids: list[UUID], archive: Archive) -> Iterable[bytes]:
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
