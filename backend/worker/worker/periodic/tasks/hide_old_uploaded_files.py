import logging
from datetime import datetime, timedelta

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_file_repository
from common.models.es_repository import PointInTimeExpiredError
from common.services.query_builder import SCAN_PIT_KEEPALIVE, QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

from worker.index_file.dispatch_tasks import dispatch_update_for_files
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return hide_old_uploaded_files_task.s()


# A lapsed point-in-time is transient: the sweep succeeds against a fresh snapshot.
# Retrying restarts the scan from the beginning, which is the only correct way to
# finish it — resuming across snapshots would skip or duplicate files.
@app.task(
    base=PeriodicTask,
    autoretry_for=(PointInTimeExpiredError,),
    retry_backoff=True,
)
def hide_old_uploaded_files_task(
    days_before_hidden: int | None = settings.uploaded_files_days_before_hidden,
):
    if days_before_hidden is None:
        return
    logger.info("Hiding old uploaded files")

    current_datetime = datetime.now()
    cutoff_date = current_datetime - timedelta(days=days_before_hidden)
    file_repository = get_file_repository()
    cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")

    # Both halves of the snapshot's lifetime are set here: open_point_in_time gives it
    # its initial one, and keep_alive is what every page extends it by.
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(keep_alive=SCAN_PIT_KEEPALIVE),
        keep_alive=SCAN_PIT_KEEPALIVE,
        search_string=f"uploaded:[* TO {cutoff_date_str}] AND hidden:false",
    )

    dispatch_update_for_files.s(query, UpdateFileRequest(hidden=True)).delay().forget()
