import logging
from itertools import islice

from celery.canvas import Signature, group
from common.dependencies import (
    get_celery_app,
    get_file_repository,
)
from common.models.es_repository import SortingParameters
from common.services.query_builder import QueryParameters

from worker.index_file.index_file_task import dispatch_reindex_file
from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()

MAX_REINDEX_FILES = 100
MAX_REINDEX_COUNT = 5


def signature() -> Signature:
    return reindex_started_files.s()


@app.task(bind=True, base=PeriodicTask)
def reindex_started_files(self: PeriodicTask, *_, **__):
    logger.info("Reindexing files")
    file_repository = get_file_repository()
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
        search_string=f"state:started AND reindex_count:<{MAX_REINDEX_COUNT}",
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
                MAX_REINDEX_FILES,
            )
        )
    )
