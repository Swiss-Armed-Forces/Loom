from common.dependencies import get_archive_scheduling_service, get_celery_app
from common.services.lazybytes_service import FileStorageLazyBytes

app = get_celery_app()


@app.task()
def dispatch_index_archive(file_content: FileStorageLazyBytes):
    """Dispatch a loom archive for import via ArchiveSchedulingService."""
    get_archive_scheduling_service().index_archive(file_content)
