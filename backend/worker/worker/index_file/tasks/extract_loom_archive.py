import logging
from zipfile import ZipFile

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_scheduling_service,
    get_lazybytes_service,
)
from common.services.encryption_service import FileEncryptionServiceException
from common.services.lazybytes_service import LazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask

ARCHIVE_IMPORT_SOURCE_ID = "archive-import"

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(file_content: LazyBytes) -> Signature:
    """Decrypt and import an LOOM archive."""
    return chain(decrypt_archive.s(file_content), unzip_loom_archive.s())


@app.task(base=FileIndexingTask)
def decrypt_archive(encrypted_file: LazyBytes) -> LazyBytes | None:
    lazybytes_service = get_lazybytes_service()
    archive_encryption_service = get_archive_encryption_service()

    with lazybytes_service.load_file(encrypted_file) as fd:
        try:
            with archive_encryption_service.get_decryptor(fd) as decryptor:

                def decrypt_generator():
                    while True:
                        decrypted = decryptor()
                        if decrypted == b"":
                            return
                        yield decrypted

                return lazybytes_service.from_generator(decrypt_generator())
        except FileEncryptionServiceException:
            # not an archive we can decrypt
            return None


@app.task(base=FileIndexingTask)
def unzip_loom_archive(decrypted_archive: LazyBytes | None):
    if decrypted_archive is None:
        return

    file_scheduling_service = get_file_scheduling_service()
    lazybytes_service = get_lazybytes_service()

    with lazybytes_service.load_file(decrypted_archive) as fd, ZipFile(fd) as zip_file:
        for fname in zip_file.namelist():
            with zip_file.open(fname, mode="r") as zipfd:
                file_scheduling_service.index_file(
                    fname,
                    lazybytes_service.from_file(zipfd),
                    ARCHIVE_IMPORT_SOURCE_ID,
                )
