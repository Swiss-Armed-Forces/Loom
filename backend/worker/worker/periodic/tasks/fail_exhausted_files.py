import logging
from itertools import islice

from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
)
from common.models.es_repository import PointInTimeExpiredError, SortingParameters
from common.services.query_builder import SCAN_PIT_KEEPALIVE, QueryParameters

from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.periodic.infra.periodic_task import PeriodicTask
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

FAILED_STATE = "failed"

# The complement of `reindex_lost_files.LOST_FILES_QUERY`: a file still short of a
# terminal state, whose reindex budget is spent. The sweep that would have finished it
# no longer selects it, and no task is left anywhere that names it.
EXHAUSTED_FILES_QUERY = (
    f'NOT state:("{FAILED_STATE}" OR "processed")'
    f" AND reindex_count:>={settings.max_reindex_count}"
)


def signature() -> Signature:
    return fail_exhausted_files.s()


# A lapsed point-in-time is transient: the sweep succeeds against a fresh snapshot.
# Retrying restarts the scan from the beginning, which is the only correct way to
# finish it — resuming across snapshots would skip or duplicate files.
@app.task(
    base=PeriodicTask,
    autoretry_for=(PointInTimeExpiredError,),
    retry_backoff=True,
)
def fail_exhausted_files() -> None:
    """Record the verdict on files the reindex sweep has given up on.

    Giving up is what `max_reindex_count` is for, but on its own it is silent: the
    `reindex_count` clause drops such a file out of the sweep and out of the completion
    estimate's pending count while its own state still says it is being worked on, so
    the work it stands for is carried by neither the pending count nor the failed one.
    Writing the state down puts it in the failed count, where a user can search for it.

    The verdict is dispatched to the file's own persister shard rather than written
    here: that shard is the one place a file's document is mutated, so a verdict that
    goes through it is merged with whatever else the pipeline is writing instead of
    landing on top of it.

    This runs behind `wait_for_processing_idle()`, which is what makes it safe: a file
    that has just spent its last reindex may still be in the pipeline, and only idle
    says it is not.
    """
    logger.info("Failing files whose reindex budget is spent")
    file_repository = get_file_repository()
    # Both halves of the snapshot's lifetime are set here: open_point_in_time gives it
    # its initial one, and keep_alive is what every page extends it by.
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(keep_alive=SCAN_PIT_KEEPALIVE),
        keep_alive=SCAN_PIT_KEEPALIVE,
        search_string=EXHAUSTED_FILES_QUERY,
    )
    sort_params = SortingParameters(
        sort_by_field="uploaded_datetime", sort_direction="desc"
    )

    # Bounded by the same setting as the reindex sweep, and for the same reason: one
    # pass of a nightly job should not hold a point in time open across an unbounded
    # number of dispatches. What is left over is picked up by the next pass.
    dispatched = 0
    for entry in islice(
        file_repository.get_id_generator_by_query(query=query, sort_params=sort_params),
        settings.reindex_lost_files_max_files,
    ):
        persist_file_failed.s(entry.id_).delay().forget()
        dispatched += 1

    if dispatched:
        logger.warning(
            "Failing %d file(s): reindexed %d times without completing",
            dispatched,
            settings.max_reindex_count,
        )


@persisting_task(app, IndexingPersister)
def persist_file_failed(persister: IndexingPersister) -> None:
    """Persist the failed state on the file the persister owns."""
    persister.set_state(FAILED_STATE)
