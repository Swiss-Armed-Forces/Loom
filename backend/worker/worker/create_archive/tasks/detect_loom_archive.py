import logging

from common.archive.archive_detection import is_loom_archive
from common.dependencies import get_celery_app, get_file_storage_service
from common.services.lazybytes_service import FileStorageLazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=FileIndexingTask)
def detect_loom_archive(
    file: FileStorageLazyBytes | None,
) -> FileStorageLazyBytes | None:
    """Return file if it contains a valid loom MANIFEST.json, else None."""
    if file is None:
        return None

    with get_file_storage_service().load_file(file) as fd:
        return file if is_loom_archive(fd) else None
