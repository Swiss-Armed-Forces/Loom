from bson import ObjectId
from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
)

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

app = get_celery_app()


@app.task(
    base=ArchiveProcessingTask,
)
def encrypt_file_task(storage_id: ObjectId) -> ObjectId:
    """Load files from storage and encryptes it.

    :param storage_id: The file storage id for the file to encrypt
    """

    file_storage_service = get_file_storage_service()
    archive_encryption_service = get_archive_encryption_service()

    encrypted_file_storage_id = ObjectId()

    with file_storage_service.open_download_stream(
        storage_id
    ) as plain_file_storage_stream, file_storage_service.open_upload_stream_with_id(
        encrypted_file_storage_id,
        "",
    ) as encrypted_file_storage_stream, archive_encryption_service.get_encryptor(
        encrypted_file_storage_stream
    ) as encrypt:
        for chunk in plain_file_storage_stream:
            encrypt(chunk)
    return encrypted_file_storage_id
