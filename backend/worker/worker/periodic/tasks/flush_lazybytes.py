import logging

from celery.canvas import Signature  # type: ignore[import-untyped]
from common.dependencies import get_celery_app, get_lazybytes_service

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return flush_lazybytes.s()


@app.task(base=PeriodicTask)
def flush_lazybytes(*_, **__):
    logger.info("Flushing lazybytes")
    get_lazybytes_service().flush()
