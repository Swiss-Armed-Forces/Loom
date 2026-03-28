from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
)
from common.services.lazybytes_service import LazyBytes

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

app = get_celery_app()


@app.task(
    base=ArchiveProcessingTask,
)
def encrypt_file_task(storage_data: LazyBytes) -> LazyBytes:
    """Load files from storage and encryptes it.

    :param storage_data: The file storage id for the file to encrypt
    """

    file_storage_service = get_file_storage_service()
    archive_encryption_service = get_archive_encryption_service()

    data_stream = file_storage_service.load_generator(storage_data)
    data_stream_encrypted = archive_encryption_service.get_encrypted_stream(data_stream)

    encrypted_storage_data = file_storage_service.from_generator(data_stream_encrypted)
    return encrypted_storage_data
