import logging

from celery import chain
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import unsubscribe_old_imap_folders

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def old_imap_folders_unsubscribed(*_, **__):
    logger.info("Old IMAP folders successfully unsubscribed")


@app.task(base=PeriodicTask)
def unsubscribe_old_imap_folders_periodically_task():
    chain(
        unsubscribe_old_imap_folders.signature(),
        old_imap_folders_unsubscribed.s(),
    ).delay().forget()
