import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_redis_client
from common.utils.cache import CACHE_KEY_PREFIX

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return flush_cache.s()


@app.task(base=PeriodicTask)
def flush_cache(*_, **__):
    logger.info("Flushing cache")
    keys_to_delete = get_redis_client().keys(f"*{CACHE_KEY_PREFIX}*")
    logger.info(keys_to_delete)
    for key in keys_to_delete:
        get_redis_client().delete(key)
