import logging

from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
)
from common.services.encryption_service import FileEncryptionServiceException
from common.services.lazybytes_service import FileStorageLazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def load_loom_archive_encrypted(
    encrypted_file: FileStorageLazyBytes,
) -> FileStorageLazyBytes | None:
    """Decrypt an encrypted loom archive; return decrypted bytes or None."""
    file_storage_service = get_file_storage_service()
    archive_encryption_service = get_archive_encryption_service()

    try:
        encrypted_generator = file_storage_service.load_generator(encrypted_file)
        decrypted_stream = archive_encryption_service.get_decrypted_stream(
            encrypted_generator
        )
        logger.info("Successfully decrypted loom archive")
        return file_storage_service.from_generator(decrypted_stream)
    except FileEncryptionServiceException:
        logger.debug("Archive is not encrypted or decryption failed, skipping")
        return None
