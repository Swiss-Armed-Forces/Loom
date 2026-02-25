import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_redis_cache_client
from common.utils.cache import shrink_cache as do_shrink_cache

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return shrink_cache.s()


@app.task(base=PeriodicTask)
def shrink_cache(*_, **__):
    logger.info("Shrinking cache")
    redis_client = get_redis_cache_client()
    do_shrink_cache(redis_client)
