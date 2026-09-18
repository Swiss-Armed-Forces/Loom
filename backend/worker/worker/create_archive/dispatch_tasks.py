from common.dependencies import get_archive_scheduling_service, get_celery_app
from common.services.task_scheduling_service import ArchiveImportRequest

app = get_celery_app()


@app.task()
def dispatch_index_archive(request: ArchiveImportRequest):
    """Dispatch a loom archive for import via ArchiveSchedulingService."""
    get_archive_scheduling_service().index_archive(request)
