import logging
from uuid import UUID
from zipfile import ZipFile

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
    get_lazybytes_service,
    get_task_scheduling_service,
)
from common.file.file_repository import File
from common.services.encryption_service import FileEncryptionServiceException
from common.services.lazybytes_service import TempLazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask

ARCHIVE_IMPORT_SOURCE_ID = "archive-import"

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(file: File, file_content: TempLazyBytes) -> Signature:
    """Decrypt and import archive."""
    return chain(
        decrypt_archive.s(file_content),
        unzip_loom_archive.s(file.id_, file.recursion_depth + 1),
    )


@app.task(base=FileIndexingTask)
def decrypt_archive(encrypted_file: TempLazyBytes) -> TempLazyBytes | None:
    lazybytes_service = get_lazybytes_service()
    archive_encryption_service = get_archive_encryption_service()

    try:
        encrypted_generator = lazybytes_service.load_generator(encrypted_file)
        decrypted_stream = archive_encryption_service.get_decrypted_stream(
            encrypted_generator
        )
        return lazybytes_service.from_generator(decrypted_stream)
    except FileEncryptionServiceException:
        # not an archive we can decrypt
        return None


@app.task(base=FileIndexingTask)
def unzip_loom_archive(
    decrypted_archive: TempLazyBytes | None,
    parent_file_id: UUID,
    recursion_depth: int = 0,
):
    if decrypted_archive is None:
        return

    lazybytes_service = get_lazybytes_service()
    file_storage_service = get_file_storage_service()
    task_scheduling_service = get_task_scheduling_service()

    with lazybytes_service.load_file(decrypted_archive) as fd, ZipFile(fd) as zip_file:
        for fname in zip_file.namelist():
            with zip_file.open(fname, mode="r") as zipfd:
                # Store in file_storage_service (permanent), not lazybytes
                file_content = file_storage_service.from_file(zipfd)
                # Dispatch task to index the file
                task_scheduling_service.dispatch_index_file(
                    full_name=fname,
                    file_content=file_content,
                    source_id=ARCHIVE_IMPORT_SOURCE_ID,
                    parent_id=parent_file_id,
                    recursion_depth=recursion_depth,
                )
