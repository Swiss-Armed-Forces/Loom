import logging

from common.dependencies import get_celery_app, get_complete_estimate_service

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def compute_complete_estimate_task():
    get_complete_estimate_service().compute_and_store()
