import datetime

from bson import ObjectId
from common.dependencies import get_celery_app, get_file_storage_service
from common.file.file_repository import File
from stream_zip import ZIP_32, stream_zip

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

app = get_celery_app()


def _archive_data(files: list[File]):
    file_storage_service = get_file_storage_service()
    modified_at = datetime.datetime.now()
    perms = 0o600

    for file in files:

        def content(file_storage_id: ObjectId):
            file_stream = file_storage_service.open_download_stream(file_storage_id)
            while True:
                data = file_stream.readchunk()
                if data == b"":
                    return
                yield data

        yield (
            str(file.full_path),
            modified_at,
            perms,
            ZIP_32,
            content(ObjectId(file.storage_id)),
        )


@app.task(
    base=ArchiveProcessingTask,
)
def compress_files_task(files: list[File]) -> ObjectId:
    """Load files from storage and compress them.

    :param files: The files to load and compress :param
    :return: the destination file
    """

    file_storage_service = get_file_storage_service()

    compressed_file_storage_id = ObjectId()
    zipped_chunks = stream_zip(_archive_data(files))

    with file_storage_service.open_upload_stream_with_id(
        compressed_file_storage_id,
        "",
    ) as zip_storage_stream:
        for chunk in zipped_chunks:
            zip_storage_stream.write(chunk)
    return compressed_file_storage_id
