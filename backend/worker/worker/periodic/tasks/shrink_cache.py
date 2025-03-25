import logging

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_redis_client
from common.utils.cache import (
    CACHE_DEFAULT_MAX_SIZE,
    CACHE_DEFAULT_SHRINK_PERCENTAGE,
    CACHE_KEY_FORMAT,
    CACHE_KEY_PREFIX,
)

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return shrink_cache.s()


@app.task(base=PeriodicTask)
def shrink_cache(*_, **__):
    logger.info("Shrinking cache")
    redis_client = get_redis_client()

    keys = redis_client.keys(f"{{{CACHE_KEY_PREFIX}*[settings]?")
    keys = list(map(lambda key: key.decode(), keys))
    tasks = list(map(lambda key: key.split(":")[1][:-1], keys))

    for task in tasks:
        logger.debug("Shrinking cache of task %s", task)
        keys_key = CACHE_KEY_FORMAT.format(namespace=task, key="keys")
        vals_key = CACHE_KEY_FORMAT.format(namespace=task, key="vals")
        settings_key = CACHE_KEY_FORMAT.format(namespace=task, key="settings")

        settings = redis_client.hgetall(settings_key)
        response = {key.decode(): value.decode() for key, value in settings.items()}
        max_size = int(response.get("max_size", CACHE_DEFAULT_MAX_SIZE))
        shrink_percentage = float(
            response.get("shrink_percentage", CACHE_DEFAULT_SHRINK_PERCENTAGE)
        )

        memory_usage = redis_client.memory_usage(vals_key)
        desired_size = max_size * shrink_percentage
        while memory_usage is not None and memory_usage > desired_size:
            logger.debug(
                "Shrinking: memory usage: %d, desired size: %d",
                memory_usage,
                desired_size,
            )
            # remove the key with the lowest score
            eject = redis_client.zrange(keys_key, 0, 0)
            if not eject:
                logger.debug("Sorted set is empty, cannot shrink the cache of %s", task)
                return
            redis_client.zremrangebyrank(keys_key, 0, 0)
            redis_client.hdel(vals_key, *eject)
            memory_usage = redis_client.memory_usage(vals_key)
