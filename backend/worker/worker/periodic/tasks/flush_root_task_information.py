import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_root_task_information_repository

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return flush_root_task_information.s()


@app.task(base=PeriodicTask)
def flush_root_task_information(*_, **__):
    logger.info("Flushing root task information")
    get_root_task_information_repository().flush()
