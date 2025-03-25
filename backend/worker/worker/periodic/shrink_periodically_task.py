import logging

from celery import chain
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import shrink_cache

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def shrink_complete(*_, **__):
    logger.info("Shrinking complete")


@app.task(base=PeriodicTask)
def shrink_periodically_task():
    chain(
        shrink_cache.signature(),
        shrink_complete.s(),
    ).delay().forget()
