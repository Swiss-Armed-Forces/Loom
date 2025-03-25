import logging
from functools import wraps
from hashlib import sha256
from pickle import dumps, loads
from time import time
from typing import Callable

from common.dependencies import get_redis_client

logger = logging.getLogger(__name__)


CACHE_KEY_PREFIX = "rc"
CACHE_KEY_FORMAT = "{{rc:{namespace}}}:{key}"
CACHE_DEFAULT_SHRINK_PERCENTAGE = 0.8  # setting 0.8 means that it will free up 20%
CACHE_DEFAULT_MAX_SIZE = 5 * (1024**3)  # 5 GB


def _default_key_function(*args, **kwargs) -> tuple:
    return (args, kwargs)


def _full_prefix(namespace: str) -> str:
    # Redis cluster requires keys operated in batch to be in the same key space.
    # Redis cluster hashes the keys to determine the key space. The braces
    # specify which part of the key to hash (instead of the whole key). See
    # https://github.com/taylorhakes/python-redis-cache/issues/29  The
    # `{prefix}:keys` and `{prefix}:args` need to be in the same key space.
    return f"{{{CACHE_KEY_PREFIX}:{namespace}}}"


def _get_key(
    key_function: Callable | None, namespace: str, args: tuple, kwargs: dict
) -> str:
    if key_function is None:
        key_function = _default_key_function
    key = key_function(*args, **kwargs)
    logger.debug("Cache key generated: %s", key)
    hash_object = sha256(dumps(key))
    identifier = hash_object.hexdigest()
    return CACHE_KEY_FORMAT.format(namespace=namespace, key=identifier)


def persisting_cache(*args, **kwargs):
    def decorator(func: Callable):
        namespace = f"{func.__module__}.{func.__qualname__}"
        nonlocal kwargs
        kwargs = {**kwargs, **{"namespace": namespace}}
        return cache(*args, **kwargs)

    return decorator


def cache(
    max_size: int = CACHE_DEFAULT_MAX_SIZE,  # 5 GB
    shrink_percentage: float = CACHE_DEFAULT_SHRINK_PERCENTAGE,
    key_function: Callable | None = None,
    namespace: str | None = None,
):
    def decorator(func: Callable):
        nonlocal namespace
        if namespace is None:
            namespace = f"{func.__module__}.{func.__qualname__}"

        keys_key = f"{_full_prefix(namespace)}:keys"
        vals_key = f"{_full_prefix(namespace)}:vals"
        stats_hit_key = f"{_full_prefix(namespace)}:hits"
        stats_miss_key = f"{_full_prefix(namespace)}:miss"
        settings_key = f"{_full_prefix(namespace)}:settings"

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _get_key(key_function, namespace, args, kwargs)
            result = None

            # retrieve the value from redis by key
            redis_client = get_redis_client()
            result = redis_client.hget(vals_key, key)

            logger.debug("Result from redis (key: %s) %s", key, result)

            if result:
                # increment hits stats
                redis_client.incr(stats_hit_key)
                # for LRU: increment score of key in keys set
                redis_client.zadd(keys_key, {key: time()})
                parsed_result = loads(result)
            else:
                parsed_result = func(*args, **kwargs)
                result_serialized = dumps(parsed_result)
                logger.debug("Serialized result %s", result_serialized)
                # store max size and shrink setting for periodic task
                redis_client.hset(settings_key, "max_size", max_size)
                redis_client.hset(settings_key, "shrink_percentage", shrink_percentage)
                # increment miss stats
                redis_client.incr(stats_miss_key)
                # for LRU: increment score of key in keys set
                redis_client.zadd(keys_key, {key: time()})
                # store result for key in cache
                redis_client.hset(vals_key, key, result_serialized)

            return parsed_result

        return wrapper

    return decorator
