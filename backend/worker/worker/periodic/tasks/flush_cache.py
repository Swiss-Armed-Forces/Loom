import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_redis_cache_client
from common.utils.cache import CACHE_KEY_PREFIX, CACHE_SCAN_COUNT

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return flush_cache.s()


@app.task(base=PeriodicTask)
def flush_cache(*_, **__):
    logger.info("Flushing cache")
    client = get_redis_cache_client()
    pipe = client.pipeline()
    count = 0
    for key in client.scan_iter(f"*{CACHE_KEY_PREFIX}*", count=CACHE_SCAN_COUNT):
        pipe.delete(key)
        count += 1
        if count % CACHE_SCAN_COUNT == 0:
            pipe.execute()
            pipe = client.pipeline()
    if count % CACHE_SCAN_COUNT != 0:
        pipe.execute()
    logger.info("Flushed %d cache keys", count)
