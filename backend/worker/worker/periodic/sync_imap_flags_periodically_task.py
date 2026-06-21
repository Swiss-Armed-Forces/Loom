import logging

from celery import chain
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import sync_imap_flags

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def sync_complete_task(*_, **__):
    logger.info("IMAP flag synchronization complete")


@app.task(base=PeriodicTask)
def sync_imap_flags_periodically_task():
    chain(
        sync_imap_flags.signature(),
        sync_complete_task.s(),
    ).delay().forget()
