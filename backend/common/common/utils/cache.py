import logging
from functools import wraps
from hashlib import sha256
from pickle import dumps, loads
from time import time
from typing import Callable

from pydantic import BaseModel, Field, RootModel, computed_field
from redis import StrictRedis

from common.dependencies import get_redis_client

logger = logging.getLogger(__name__)


CACHE_KEY_PREFIX = "rc"
CACHE_KEY_FORMAT = "{{rc:{namespace}}}:{key}"
CACHE_DEFAULT_SHRINK_PERCENTAGE = 0.8  # setting 0.8 means that it will free up 20%
CACHE_DEFAULT_TTL_SECONDS = 3600  # 60 minutes
CACHE_DEFAULT_MAX_SIZE = 5 * (1024**3)  # 5 GB


class CacheStatisticsEntryModel(BaseModel):
    """Cache stats of task caching."""

    mem_size: int
    entries_count: int
    hits_count: int
    miss_count: int


class CacheStatistics(RootModel):
    root: dict[str, CacheStatisticsEntryModel] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def mem_size_total(self) -> int:
        return sum(entry.mem_size for entry in self.root.values())

    @computed_field  # type: ignore[misc]
    @property
    def entries_count_total(self) -> int:
        return sum(entry.entries_count for entry in self.root.values())

    @computed_field  # type: ignore[misc]
    @property
    def hits_count_total(self) -> int:
        return sum(entry.hits_count for entry in self.root.values())

    @computed_field  # type: ignore[misc]
    @property
    def miss_count_total(self) -> int:
        return sum(entry.miss_count for entry in self.root.values())

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, newvalue):
        self.root[key] = newvalue


def get_cache_statistics(redis_client: StrictRedis) -> CacheStatistics:
    """Get statistics for all cache namespaces."""
    result = CacheStatistics()

    keys_bytes = redis_client.keys(f"{{{CACHE_KEY_PREFIX}*[miss|hits]?")
    keys = [key.decode() for key in keys_bytes]

    tasks = {key.split(":")[1][:-1] for key in keys}
    for task in tasks:
        val_key = CACHE_KEY_FORMAT.format(namespace=task, key="vals")
        mem_size = redis_client.execute_command(f"MEMORY USAGE {val_key}")
        entries_count = redis_client.zcard(
            CACHE_KEY_FORMAT.format(namespace=task, key="keys")
        )
        hits_count = redis_client.get(
            CACHE_KEY_FORMAT.format(namespace=task, key="hits")
        )
        miss_count = redis_client.get(
            CACHE_KEY_FORMAT.format(namespace=task, key="miss")
        )

        result[task] = CacheStatisticsEntryModel(
            mem_size=int(mem_size) if mem_size else 0,
            entries_count=int(entries_count) if entries_count else 0,
            hits_count=int(hits_count) if hits_count else 0,
            miss_count=int(miss_count) if miss_count else 0,
        )

    return result


def shrink_cache(redis_client: StrictRedis) -> None:
    """Shrink all cache namespaces that exceed their configured max size."""
    keys_bytes = redis_client.keys(f"{{{CACHE_KEY_PREFIX}*[settings]?")
    keys = [key.decode() for key in keys_bytes]
    tasks = [key.split(":")[1][:-1] for key in keys]

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
                break
            redis_client.zremrangebyrank(keys_key, 0, 0)
            redis_client.hdel(vals_key, *eject)
            memory_usage = redis_client.memory_usage(vals_key)


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
    max_size: int = CACHE_DEFAULT_MAX_SIZE,
    shrink_percentage: float = CACHE_DEFAULT_SHRINK_PERCENTAGE,
    ttl_seconds: int = CACHE_DEFAULT_TTL_SECONDS,
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

            logger.debug("Result from redis (key: %s): %s", key, bool(result))

            if result:
                # increment hits stats
                redis_client.incr(stats_hit_key)
                # for LRU: increment score of key in keys set
                redis_client.zadd(keys_key, {key: time()})
                parsed_result = loads(result)
            else:
                parsed_result = func(*args, **kwargs)
                result_serialized = dumps(parsed_result)

                # Atomically try to be the first to store this value.
                # HSETNX returns True if we stored (field was new),
                # False if someone else beat us.
                was_first = redis_client.hsetnx(vals_key, key, result_serialized)

                if was_first:
                    # We were first to cache - this is a true cache miss
                    redis_client.incr(stats_miss_key)
                    redis_client.hset(settings_key, "max_size", max_size)
                    redis_client.hset(
                        settings_key, "shrink_percentage", shrink_percentage
                    )
                    redis_client.hexpire(vals_key, ttl_seconds, key)  # type: ignore
                else:
                    # Race condition: another process computed and stored the same value
                    # between our hget check and hsetnx. We count this as a "hit" because:
                    # 1. The value WAS in cache by the time we tried to store
                    # 2. This keeps hit/miss counts deterministic for testing
                    # 3. Semantically, a "hit" means "cache had the value" which is now true
                    # Note: We still return our computed result (identical to cached value)
                    redis_client.incr(stats_hit_key)

                # LRU bookkeeping
                redis_client.zadd(keys_key, {key: time()})

            # set/refresh ttl for vals_key
            redis_client.expire(vals_key, ttl_seconds)

            return parsed_result

        return wrapper

    return decorator
