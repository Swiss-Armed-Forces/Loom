import logging
from datetime import datetime, timedelta
from typing import Literal

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_file_repository
from common.services.query_builder import QueryParameters

from worker.index_file.set_hidden_state_task import dispatch_set_hidden_state_for_files
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()

KEEP_ALIVE: Literal["10s"] = "10s"


def signature() -> Signature:
    return hide_old_uploaded_files_task.s()


@app.task(base=PeriodicTask)
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

    query = QueryParameters(
        query_id=file_repository.open_point_in_time(keep_alive=KEEP_ALIVE),
        search_string=f"uploaded:[* TO {cutoff_date_str}] AND hidden:false",
    )

    dispatch_set_hidden_state_for_files.s(query, True).delay().forget()
