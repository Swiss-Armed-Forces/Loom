import logging

from celery import chain, group
from common.dependencies import get_celery_app, get_queues_service

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import flush_cache, flush_lazybytes

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def flush_complete(*_, **__):
    logger.info("Flushing complete")


@app.task(base=PeriodicTask)
def flush_on_idle_task():
    queues_service = get_queues_service()

    if queues_service.get_message_count() > 0:
        logger.info("Queues not empty: do nothing")
        return

    logger.info("Queues empty: flush indexing data")
    chain(
        group(
            flush_cache.signature(),
            flush_lazybytes.signature(),
        ),
        flush_complete.s(),
    ).delay().forget()
