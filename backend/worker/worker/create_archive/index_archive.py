from celery import chain, group
from common.dependencies import get_celery_app
from common.services.lazybytes_service import FileStorageLazyBytes

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks import unzip_loom_archive
from worker.create_archive.tasks.detect_loom_archive import detect_loom_archive
from worker.create_archive.tasks.load_loom_archive_encrypted import (
    load_loom_archive_encrypted,
)

app = get_celery_app()


@app.task(base=ArchiveProcessingTask)
def index_archive_task(file_content: FileStorageLazyBytes):
    """Import a loom archive (plain or encrypted) without creating a File entry."""
    group(
        chain(
            load_loom_archive_encrypted.s(file_content),
            detect_loom_archive.s(),
            unzip_loom_archive.signature(encrypted_archive_zip=file_content),
        ),
        chain(
            detect_loom_archive.s(file_content),
            unzip_loom_archive.signature(),
        ),
    ).delay().forget()
