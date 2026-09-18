import logging
from functools import wraps
from hashlib import sha256
from pickle import dumps, loads
from time import monotonic
from typing import Any, Callable, Generic, NamedTuple, TypeIs, TypeVar

from pydantic import BaseModel, Field, RootModel, computed_field
from redis import StrictRedis

from common.dependencies import get_redis_cache_client

logger = logging.getLogger(__name__)

T = TypeVar("T")


CACHE_KEY_PREFIX = "rc"
CACHE_KEY_FORMAT = "{{rc:{namespace}}}:{key}"
CACHE_DEFAULT_TTL_SECONDS = 60 * 60 * 24  # 1 day
CACHE_DEFAULT_MAX_SIZE = 5 * (1024**3)  # 5 GB
CACHE_SCAN_COUNT = 200


class CacheStatisticsEntryModel(BaseModel):
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

    keys_bytes = list(
        redis_client.scan_iter(
            f"{{{CACHE_KEY_PREFIX}*[miss|hits]?", count=CACHE_SCAN_COUNT
        )
    )
    keys = [key.decode() for key in keys_bytes]

    namespaces = {":".join(key.split(":")[1:-1])[:-1] for key in keys}

    for namespace in namespaces:
        val_key = CACHE_KEY_FORMAT.format(namespace=namespace, key="vals")
        mem_size = redis_client.execute_command(f"MEMORY USAGE {val_key}")
        entries_count = redis_client.zcard(
            CACHE_KEY_FORMAT.format(namespace=namespace, key="keys")
        )
        hits_count = redis_client.get(
            CACHE_KEY_FORMAT.format(namespace=namespace, key="hits")
        )
        miss_count = redis_client.get(
            CACHE_KEY_FORMAT.format(namespace=namespace, key="miss")
        )

        result[namespace] = CacheStatisticsEntryModel(
            mem_size=int(mem_size) if mem_size else 0,
            entries_count=int(entries_count) if entries_count else 0,
            hits_count=int(hits_count) if hits_count else 0,
            miss_count=int(miss_count) if miss_count else 0,
        )

    return result


def shrink_cache(redis_client: StrictRedis) -> None:
    """Shrink all cache namespaces that exceed their configured max size."""
    keys_bytes = list(
        redis_client.scan_iter(
            f"{{{CACHE_KEY_PREFIX}*[settings]?", count=CACHE_SCAN_COUNT
        )
    )
    keys = [key.decode() for key in keys_bytes]

    namespaces = {":".join(key.split(":")[1:-1])[:-1] for key in keys}

    for namespace in namespaces:
        logger.debug("Shrinking cache '%s'", namespace)
        keys_key = CACHE_KEY_FORMAT.format(namespace=namespace, key="keys")
        vals_key = CACHE_KEY_FORMAT.format(namespace=namespace, key="vals")
        settings_key = CACHE_KEY_FORMAT.format(namespace=namespace, key="settings")

        settings = redis_client.hgetall(settings_key)
        response = {key.decode(): value.decode() for key, value in settings.items()}
        max_size = int(response.get("max_size", CACHE_DEFAULT_MAX_SIZE))

        memory_usage = redis_client.memory_usage(vals_key)
        while memory_usage is not None and memory_usage > max_size:
            logger.info(
                "Shrinking '%s': memory usage: %d, max size: %d",
                namespace,
                memory_usage,
                max_size,
            )
            # remove the key with the lowest score
            eject = redis_client.zrange(keys_key, 0, 0)
            if not eject:
                logger.debug(
                    "Sorted set is empty, cannot shrink the cache '%s'", namespace
                )
                break
            redis_client.zremrangebyrank(keys_key, 0, 0)
            redis_client.hdel(vals_key, *eject)
            memory_usage = redis_client.memory_usage(vals_key)


def _default_key_function(*args, **kwargs) -> tuple:
    return (args, kwargs)


def _is_exactly(value: Any, expected: type[T]) -> TypeIs[T]:
    """Return whether ``value`` is an ``expected`` exactly, and not a subclass."""
    return value.__class__ is expected


class _CanonicalValue(NamedTuple):
    """A container in a cache key, rewritten so equal containers pickle equal.

    Only ever handed to ``sha256(dumps(...))`` and never unpickled back into the type it
    names, so describing a container is enough — it never has to be rebuilt. Pickle
    records this class by name, so nothing a caller passes in can collide with one.
    """

    module: str
    qualname: str
    items: tuple[Any, ...]


def _canonical(value: Any, *items: Any) -> _CanonicalValue:
    return _CanonicalValue(type(value).__module__, type(value).__qualname__, items)


def _canonicalize_key(value: Any) -> Any:
    """Return a stand-in for ``value`` that pickles to the same bytes everywhere.

    ``_get_key()`` hashes ``dumps(key)``, which only identifies a cached value if equal
    keys pickle to equal bytes. Unordered containers do not: pickle writes a ``set`` in
    iteration order, which follows the interpreter's string-hash seed (different in
    every container) and, whenever two members share a bucket, the order they were
    inserted in; it writes a ``dict`` in insertion order, so ``f(a=1, b=2)`` and
    ``f(b=2, a=1)`` reach ``dumps()`` as different bytes.

    Nothing passed to a cached task is meant to carry either, but every Pydantic model
    smuggles a set in: its pickled state includes ``__pydantic_fields_set__``. Two
    processes therefore derived two different keys for the very same model, and neither
    could read what the other had cached — one extra entry, one extra miss, once per
    argument that happened to be a model.

    So every container becomes a ``_CanonicalValue``: sets and dicts ordered by the
    pickled bytes of their members, models reduced to their field values.

    ``LazyBytes`` and ``TypedLazyBytes`` are untouched: they define ``__reduce__``,
    which pickles a ``model_dump()`` and never reaches the field set, and rewriting
    them here would change keys that are already stable.

    Only the exact builtin containers are descended into. A subclass may carry state
    that its contents do not show — an ``OrderedDict`` means its order, a
    ``defaultdict`` its factory — and a stand-in built from the contents alone would
    hand two of them the same key, which returns one's cached value for the other.
    Leaving them whole risks an unstable key, never a wrong one.
    """
    if isinstance(value, BaseModel) and type(value).__reduce__ is object.__reduce__:
        return _canonical(
            value,
            _canonicalize_key(vars(value)),
            _canonicalize_key(value.__pydantic_extra__),
            _canonicalize_key(value.__pydantic_private__),
        )
    if _is_exactly(value, set) or _is_exactly(value, frozenset):
        return _canonical(
            value, *sorted((_canonicalize_key(item) for item in value), key=dumps)
        )
    if _is_exactly(value, dict):
        return _canonical(
            value,
            *sorted(
                (
                    (_canonicalize_key(item_key), _canonicalize_key(item_value))
                    for item_key, item_value in value.items()
                ),
                key=dumps,
            ),
        )
    if _is_exactly(value, list) or _is_exactly(value, tuple):
        return _canonical(value, *(_canonicalize_key(item) for item in value))
    return value


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
    hash_object = sha256(dumps(_canonicalize_key(key)))
    identifier = hash_object.hexdigest()
    return CACHE_KEY_FORMAT.format(namespace=namespace, key=identifier)


class CacheResult(BaseModel, Generic[T]):
    """Result of a cache lookup."""

    hit: bool
    value: T | None = None


def cache_get(
    namespace: str,
    key_function: Callable | None,
    *args,
    **kwargs,
) -> CacheResult[Any]:
    """Get a value from the cache.

    Returns:
        CacheResult with hit=True and value if found, hit=False otherwise.
    """
    key = _get_key(key_function, namespace, args, kwargs)
    vals_key = f"{_full_prefix(namespace)}:vals"
    keys_key = f"{_full_prefix(namespace)}:keys"
    stats_hit_key = f"{_full_prefix(namespace)}:hits"
    stats_miss_key = f"{_full_prefix(namespace)}:miss"

    redis_client = get_redis_cache_client()
    result = redis_client.hget(vals_key, key)

    if result is not None:
        redis_client.incr(stats_hit_key)
        redis_client.zadd(keys_key, {key: monotonic()})
        return CacheResult(hit=True, value=loads(result))

    redis_client.incr(stats_miss_key)
    return CacheResult(hit=False)


def cache_set(
    namespace: str,
    key_function: Callable | None,
    value: Any,
    *args,
    max_size: int = CACHE_DEFAULT_MAX_SIZE,
    ttl_seconds: int = CACHE_DEFAULT_TTL_SECONDS,
    **kwargs,
) -> None:
    """Set a value in the cache."""
    key = _get_key(key_function, namespace, args, kwargs)
    vals_key = f"{_full_prefix(namespace)}:vals"
    keys_key = f"{_full_prefix(namespace)}:keys"
    settings_key = f"{_full_prefix(namespace)}:settings"

    redis_client = get_redis_cache_client()
    redis_client.hset(vals_key, key, dumps(value))
    redis_client.zadd(keys_key, {key: monotonic()})
    redis_client.hset(settings_key, "max_size", max_size)
    redis_client.hexpire(vals_key, ttl_seconds, key)  # type: ignore[attr-defined]
    redis_client.expire(vals_key, ttl_seconds)


def cache_invalidate(
    namespace: str, key_function: Callable | None, *args, **kwargs
) -> bool:
    """Invalidate (delete) a specific cache entry.

    Returns:
        True if the entry was deleted, False if it didn't exist.
    """
    key = _get_key(key_function, namespace, args, kwargs)
    keys_key = f"{_full_prefix(namespace)}:keys"
    vals_key = f"{_full_prefix(namespace)}:vals"

    redis_client = get_redis_cache_client()
    deleted = redis_client.hdel(vals_key, key)
    redis_client.zrem(keys_key, key)

    return deleted > 0


def persisting_cache(*args, **kwargs):
    def decorator(func: Callable):
        namespace = f"{func.__module__}.{func.__qualname__}"
        nonlocal kwargs
        kwargs = {**kwargs, **{"namespace": namespace}}
        return cache(*args, **kwargs)

    return decorator


def cache(
    max_size: int = CACHE_DEFAULT_MAX_SIZE,
    ttl_seconds: int = CACHE_DEFAULT_TTL_SECONDS,
    key_function: Callable | None = None,
    namespace: str | None = None,
):
    def decorator(func: Callable):
        resolved_namespace = namespace
        if resolved_namespace is None:
            resolved_namespace = f"{func.__module__}.{func.__qualname__}"

        keys_key = f"{_full_prefix(resolved_namespace)}:keys"
        vals_key = f"{_full_prefix(resolved_namespace)}:vals"
        stats_hit_key = f"{_full_prefix(resolved_namespace)}:hits"
        stats_miss_key = f"{_full_prefix(resolved_namespace)}:miss"
        settings_key = f"{_full_prefix(resolved_namespace)}:settings"

        @wraps(func)
        def wrapper(*args, **kwargs):
            assert resolved_namespace is not None
            key = _get_key(key_function, resolved_namespace, args, kwargs)
            result = None

            # retrieve the value from redis by key
            redis_client = get_redis_cache_client()
            result = redis_client.hget(vals_key, key)

            logger.debug("Result from redis (key: %s): %s", key, bool(result))

            if result:
                # increment hits stats
                redis_client.incr(stats_hit_key)
                # for LRU: increment score of key in keys set
                redis_client.zadd(keys_key, {key: monotonic()})
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
                redis_client.zadd(keys_key, {key: monotonic()})

            # set/refresh ttl for vals_key
            redis_client.expire(vals_key, ttl_seconds)

            return parsed_result

        return wrapper

    return decorator
