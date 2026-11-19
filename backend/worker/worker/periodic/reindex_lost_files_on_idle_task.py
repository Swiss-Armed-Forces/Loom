import logging

from celery import chain
from common.dependencies import get_celery_app, get_celery_inspect_service

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import fail_exhausted_files, reindex_lost_files

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def reindex_lost_files_on_idle_complete(*_, **__):
    logger.info("Reindex started files complete")


@app.task(base=PeriodicTask)
def reindex_lost_files_on_idle_task():
    if not get_celery_inspect_service().wait_for_processing_idle():
        logger.info("Celery not idle: timed out waiting for idle")
        return

    logger.info("Queues empty: Reindex started files")
    # The verdict comes before the sweep, so a file is only failed on a pass that did
    # not just hand it another attempt: this pass fails what the previous one left
    # without budget, and spends the budget of what is still inside it.
    chain(
        fail_exhausted_files.signature(),
        reindex_lost_files.signature(),
        reindex_lost_files_on_idle_complete.s(),
    ).delay().forget()
