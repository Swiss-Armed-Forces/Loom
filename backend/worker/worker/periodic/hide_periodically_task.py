import logging

from celery import chain
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import hide_old_uploaded_files

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def old_files_hidden(*_, **__):
    logger.info("Old files successfully hidden")


@app.task(base=PeriodicTask)
def hide_periodically_task():
    chain(
        hide_old_uploaded_files.hide_old_uploaded_files_task.signature(),
        old_files_hidden.s(),
    ).delay().forget()
