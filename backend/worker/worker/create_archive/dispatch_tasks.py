from common.celery_app import TaskGroupName, task_group
from common.dependencies import get_archive_scheduling_service, get_celery_app
from common.services.task_scheduling_service import ArchiveImportRequest

app = get_celery_app()


# In DISPATCH, like `index_file/dispatch_tasks.py`'s sibling, because this is an
# ingest root of its own: the crawler routes every archive-shaped object in the intake
# bucket through here -- every archive on a USB stick, unattended. `set_throttled(True)`
# pauses only that group, so outside it the throttle cannot "stop new file ingestion
# pipelines at the root" while the unpack keeps filling `tempfile_dir`; and a task
# outside DISPATCH is also outside `exclude_tasks`, so its queue has to drain before
# `wait_for_idle` returns -- while the crawler keeps refilling it.
@task_group(TaskGroupName.DISPATCH)
@app.task()
def dispatch_index_archive(request: ArchiveImportRequest) -> None:
    """Dispatch a loom archive for import via ArchiveSchedulingService."""
    get_archive_scheduling_service().index_archive(request)
