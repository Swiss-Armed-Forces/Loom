import logging

from celery import chain, group
from common.dependencies import get_celery_app
from common.utils.celery_inspect import is_celery_idle

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import flush_cache, flush_lazybytes

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def flush_complete(*_, **__):
    logger.info("Flushing complete")


@app.task(base=PeriodicTask)
def flush_on_idle_task():
    if is_celery_idle(called_from_task=True):
        logger.info("Celery not idle: do nothing")
        return

    logger.info("Queues empty: flush indexing data")
    chain(
        group(
            flush_cache.signature(),
            flush_lazybytes.signature(),
        ),
        flush_complete.s(),
    ).delay().forget()
