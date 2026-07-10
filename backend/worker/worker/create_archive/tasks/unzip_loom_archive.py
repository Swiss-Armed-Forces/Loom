import logging
from uuid import UUID
from zipfile import ZipFile

from celery import chain, group
from common.archive.archive_repository import ARCHIVE_STATE_IMPORTED, Archive
from common.dependencies import (
    get_archive_repository,
    get_celery_app,
    get_file_repository,
    get_file_storage_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import FileStorageLazyBytes

from worker.create_archive.tasks import calculate_checksum, calculate_size
from worker.create_archive.tasks.archive_cli import (
    FILES_DIR,
    FILES_INDEX_DIR,
    JSON_SUFFIX,
    MANIFEST_FILENAME,
)
from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(encrypted_archive_zip: FileStorageLazyBytes | None = None):
    """Return a canvas that unpacks a loom archive (receives FileStorageLazyBytes|None
    from chain)."""
    return group(
        chain(
            restore_archive_metadata_task.s(
                encrypted_archive_zip=encrypted_archive_zip
            ),
            dispatch_archive_file_stats_task.s(),
        ),
        store_raw_files_task.s(),
        upsert_file_objects_task.s(),
    )


@app.task(base=FileIndexingTask)
def restore_archive_metadata_task(
    archive_zip: FileStorageLazyBytes | None,
    encrypted_archive_zip: FileStorageLazyBytes | None = None,
) -> Archive | None:
    if archive_zip is None:
        return None
    with get_file_storage_service().load_file(archive_zip) as fd:
        with ZipFile(fd) as zf:
            manifest_entry = next(
                (n for n in zf.namelist() if n.endswith(f"/{MANIFEST_FILENAME}")), None
            )
            if manifest_entry is None:
                return None
            archive = Archive.model_validate_json(zf.read(manifest_entry))
    archive.state = ARCHIVE_STATE_IMPORTED
    archive.plain_file.storage_data = archive_zip
    archive.encrypted_file.storage_data = encrypted_archive_zip
    get_archive_repository().save(archive)
    logger.info("Restored archive metadata from MANIFEST.json")
    return archive


@app.task(base=FileIndexingTask)
def dispatch_archive_file_stats_task(
    archive: Archive | None,
) -> None:
    if archive is None:
        return
    archive_zip = archive.plain_file.storage_data
    if archive_zip is None:
        return

    logger.info("Dispatching checksum and size tasks for plain archive %s", archive.id_)
    group(
        calculate_checksum.signature_plain_file(archive.id_),
        calculate_size.signature_plain_file(archive.id_),
    ).apply_async(args=(archive_zip,)).forget()

    if archive.encrypted_file.storage_data is not None:
        logger.info(
            "Dispatching checksum and size tasks for encrypted archive %s", archive.id_
        )
        group(
            calculate_checksum.signature_encrypted_file(archive.id_),
            calculate_size.signature_encrypted_file(archive.id_),
        ).apply_async(args=(archive.encrypted_file.storage_data,)).forget()


@app.task(base=FileIndexingTask)
def store_raw_files_task(archive_zip: FileStorageLazyBytes | None) -> None:
    if archive_zip is None:
        return
    file_storage_service = get_file_storage_service()
    count = 0
    with file_storage_service.load_file(archive_zip) as fd:
        with ZipFile(fd) as zf:
            for fname in zf.namelist():
                _, _, relative = fname.partition("/")
                if relative.startswith(f"{FILES_DIR}/"):
                    service_id = UUID(relative[len(FILES_DIR) + 1 :])
                    with zf.open(fname, mode="r") as zipfd:
                        file_storage_service.from_file_with_id(zipfd, service_id)
                    count += 1
    logger.info("Stored %d raw file(s) from archive", count)


@app.task(base=FileIndexingTask)
def upsert_file_objects_task(archive_zip: FileStorageLazyBytes | None) -> None:
    if archive_zip is None:
        return
    file_repository = get_file_repository()
    count = 0
    with get_file_storage_service().load_file(archive_zip) as fd:
        with ZipFile(fd) as zf:
            for fname in zf.namelist():
                _, _, relative = fname.partition("/")
                if relative.startswith(f"{FILES_INDEX_DIR}/") and relative.endswith(
                    JSON_SUFFIX
                ):
                    file_id = UUID(
                        relative[len(FILES_INDEX_DIR) + 1 : -len(JSON_SUFFIX)]
                    )
                    with zf.open(fname, mode="r") as zipfd:
                        file = File.model_validate_json(zipfd.read())
                        file.id_ = file_id
                        file_repository.save(file)
                    count += 1
    logger.info("Upserted %d file object(s) into repository", count)
