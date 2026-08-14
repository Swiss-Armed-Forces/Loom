import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return beat_healthcheck_task.s()


@app.task(base=PeriodicTask)
def beat_healthcheck_task():
    pass
