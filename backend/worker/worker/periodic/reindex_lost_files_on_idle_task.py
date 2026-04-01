import logging

from celery import chain
from common.dependencies import get_celery_app
from common.utils.celery_inspect import is_celery_idle

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import reindex_lost_files

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def reindex_lost_files_on_idle_complete(*_, **__):
    logger.info("Reindex started files complete")


@app.task(base=PeriodicTask)
def reindex_lost_files_on_idle_task():
    if is_celery_idle(called_from_task=True):
        logger.info("Celery not idle: do nothing")
        return

    logger.info("Queues empty: Reindex started files")
    chain(
        reindex_lost_files.signature(),
        reindex_lost_files_on_idle_complete.s(),
    ).delay().forget()
