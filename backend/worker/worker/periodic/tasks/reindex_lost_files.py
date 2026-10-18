import logging
from itertools import islice

from celery import group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
)
from common.models.es_repository import PointInTimeExpiredError, SortingParameters
from common.services.query_builder import SCAN_PIT_KEEPALIVE, QueryParameters

from worker.index_file.dispatch_tasks import dispatch_reindex_file
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()

LOST_FILES_QUERY = (
    f'NOT state:("failed" OR "processed")'
    f" AND reindex_count:<{settings.max_reindex_count}"
)


def signature() -> Signature:
    return reindex_lost_files.s()


# A lapsed point-in-time is transient: the sweep succeeds against a fresh snapshot.
# Retrying restarts the scan from the beginning, which is the only correct way to
# finish it — resuming across snapshots would skip or duplicate files.
@app.task(
    bind=True,
    base=PeriodicTask,
    autoretry_for=(PointInTimeExpiredError,),
    retry_backoff=True,
)
def reindex_lost_files(self: PeriodicTask, *_, **__):
    logger.info("Reindexing files")
    file_repository = get_file_repository()
    # Both halves of the snapshot's lifetime are set here: open_point_in_time gives it
    # its initial one, and keep_alive is what every page extends it by.
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(keep_alive=SCAN_PIT_KEEPALIVE),
        keep_alive=SCAN_PIT_KEEPALIVE,
        search_string=LOST_FILES_QUERY,
    )
    sort_params = SortingParameters(
        sort_by_field="uploaded_datetime", sort_direction="desc"
    )

    self.replace(
        group(
            dispatch_reindex_file.s(file_id=file.id_)
            for file in islice(
                file_repository.get_id_generator_by_query(
                    query=query, sort_params=sort_params
                ),
                settings.reindex_lost_files_max_files,
            )
        )
    )
