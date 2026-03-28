import datetime
import logging

from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from stream_zip import ZIP_32, stream_zip

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def _archive_data(files: list[File]):
    file_storage_service = get_file_storage_service()
    modified_at = datetime.datetime.now()
    perms = 0o600

    for file in files:
        if file.storage_data is None:
            logger.warning(
                "Skipping file '%s' from archive: no storage data",
                file.full_path,
            )
            continue

        yield (
            str(file.full_path),
            modified_at,
            perms,
            ZIP_32,
            file_storage_service.load_generator(file.storage_data),
        )


@app.task(
    base=ArchiveProcessingTask,
)
def compress_files_task(files: list[File]) -> LazyBytes:
    """Load files from storage and compress them.

    :param files: The files to load and compress :param
    :return: the destination file
    """

    file_storage_service = get_file_storage_service()

    zipped_chunks = stream_zip(_archive_data(files))

    compressed_file_storage_data = file_storage_service.from_generator(
        iter(zipped_chunks)
    )
    return compressed_file_storage_data
