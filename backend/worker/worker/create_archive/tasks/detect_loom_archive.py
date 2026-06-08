import logging
from zipfile import BadZipFile, ZipFile

from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive
from common.dependencies import get_celery_app, get_file_storage_service
from common.services.lazybytes_service import FileStorageLazyBytes
from pydantic import ValidationError

from worker.create_archive.tasks.archive_format import MANIFEST_FILENAME
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

    try:
        with get_file_storage_service().load_file(file) as fd, ZipFile(fd) as zf:
            manifest_entry = next(
                (n for n in zf.namelist() if n.endswith(f"/{MANIFEST_FILENAME}")), None
            )
            if manifest_entry is None:
                return None
            manifest = Archive.model_validate_json(zf.read(manifest_entry))
            if manifest.version != LOOM_ARCHIVE_VERSION:
                logger.warning("Unsupported loom archive version: %s", manifest.version)
                return None
            return file
    except (BadZipFile, ValidationError, OSError):
        return None
