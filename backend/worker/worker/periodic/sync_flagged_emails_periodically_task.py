import logging

from celery import chain
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import sync_flagged_emails

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def sync_complete(*_, **__):
    logger.info("Flagged emails synchronization complete")


@app.task(base=PeriodicTask)
def sync_flagged_emails_periodically_task():
    chain(
        sync_flagged_emails.signature(),
        sync_complete.s(),
    ).delay().forget()
