import logging

from celery import chain
from common.dependencies import get_celery_app, get_queues_service

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import reindex_started_files

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def reindex_started_files_on_idle_complete(*_, **__):
    logger.info("Reindex started files complete")


@app.task(base=PeriodicTask)
def reindex_started_files_on_idle_task():
    queues_service = get_queues_service()

    if queues_service.get_message_count() > 0:
        logger.info("Queues not empty: do nothing")
        return

    logger.info("Queues empty: Reindex started files")
    chain(
        reindex_started_files.signature(),
        reindex_started_files_on_idle_complete.s(),
    ).delay().forget()
