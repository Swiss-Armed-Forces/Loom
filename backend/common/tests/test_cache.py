from collections import OrderedDict, defaultdict
from hashlib import sha256
from pickle import dumps, loads
from uuid import UUID

from pydantic import BaseModel

from common.dependencies import get_redis_cache_client
from common.services.lazybytes_service import TempLazyBytes
from common.utils.cache import (
    CACHE_KEY_FORMAT,
    _get_key,
    cache,
    cache_get,
    cache_invalidate,
    cache_set,
)


@cache(key_function=lambda: "my-key")
def cached_function() -> str:
    return "testresult"


def test_cache_decorator():
    redis_client = get_redis_cache_client()
    # set up
    redis_client.hget.return_value = None
    redis_client.hsetnx.return_value = True  # Simulate being first to cache
    redis_client.zcard.return_value = 1

    # call function to trigger caching
    cached_function()

    # assertion
    hash_object = sha256(dumps("my-key"))
    identifier = hash_object.hexdigest()
    expected_namespace = "test_cache.cached_function"

    redis_client.hget.assert_called_once_with(
        f"{{rc:{expected_namespace}}}:vals", f"{{rc:{expected_namespace}}}:{identifier}"
    )
    assert redis_client.zadd.call_args.args[0] == f"{{rc:{expected_namespace}}}:keys"
    # Value is now stored atomically via hsetnx
    assert redis_client.hsetnx.call_args.args[0] == f"{{rc:{expected_namespace}}}:vals"
    assert (
        redis_client.hsetnx.call_args.args[1]
        == f"{{rc:{expected_namespace}}}:{identifier}"
    )
    # hset is now used for settings
    assert (
        redis_client.hset.call_args.args[0] == f"{{rc:{expected_namespace}}}:settings"
    )
    assert not redis_client.zrange.called
    assert not redis_client.zremrangebyrank.called
    assert not redis_client.hdel.called


def test_cache_get_hit():
    """Test cache_get returns hit=True with value when key exists."""
    redis_client = get_redis_cache_client()
    test_value = {"foo": "bar"}
    redis_client.hget.return_value = dumps(test_value)

    result = cache_get("test.namespace", lambda x: (x,), "key123")

    assert result.hit is True
    assert result.value == test_value
    redis_client.incr.assert_called()  # hits counter incremented


def test_cache_get_miss():
    """Test cache_get returns hit=False when key doesn't exist."""
    redis_client = get_redis_cache_client()
    redis_client.hget.return_value = None

    result = cache_get("test.namespace", lambda x: (x,), "key123")

    assert result.hit is False
    assert result.value is None


def test_cache_set():
    """Test cache_set stores value in Redis."""
    redis_client = get_redis_cache_client()
    test_value = {"data": 123}

    cache_set("test.namespace", lambda x: (x,), test_value, "key123")

    # Verify hset was called with serialized value
    assert redis_client.hset.called
    call_args = redis_client.hset.call_args_list[0]
    assert "test.namespace" in call_args.args[0]
    stored_value = loads(call_args.args[2])
    assert stored_value == test_value


def test_invalidate_existing_key():
    """Test invalidate removes key and returns True."""
    redis_client = get_redis_cache_client()
    redis_client.hdel.return_value = 1  # 1 key deleted

    result = cache_invalidate("test.namespace", lambda x: (x,), "key123")

    assert result is True
    assert redis_client.hdel.called
    assert redis_client.zrem.called


class _KeyModel(BaseModel):
    payload: TempLazyBytes
    frames: int = 0


def _fields_set_orders(model: BaseModel) -> list[BaseModel]:
    """Same model, with ``__pydantic_fields_set__`` inserted in either order.

    A two-member set whose members share a bucket iterates in insertion order, so this
    is exactly the difference two processes saw between a freshly built model and one
    restored from a pickle.
    """
    names = sorted(model.__pydantic_fields_set__)
    variants = []
    for order in (names, list(reversed(names))):
        variant = model.model_copy()
        fields_set: set[str] = set()
        for name in order:
            fields_set.add(name)
        object.__setattr__(variant, "__pydantic_fields_set__", fields_set)
        variants.append(variant)
    return variants


def test_key_is_stable_for_equal_models():
    """A model argument must produce one cache key, not one per process.

    ``dumps()`` writes ``__pydantic_fields_set__`` in set-iteration order, which follows
    the interpreter's hash seed and the insertion order. Left in the key, it made a
    worker miss on a value another worker had just cached.
    """
    model = _KeyModel(
        payload=TempLazyBytes(service_id=UUID(int=1)),
        frames=1,
    )

    keys = {
        _get_key(None, "ns", (variant,), {}) for variant in _fields_set_orders(model)
    }

    assert len(keys) == 1


def test_key_distinguishes_different_models():
    """Stability must not come from collapsing distinct arguments onto one key."""
    payload = TempLazyBytes(service_id=UUID(int=1))

    assert _get_key(
        None, "ns", (_KeyModel(payload=payload, frames=1),), {}
    ) != _get_key(None, "ns", (_KeyModel(payload=payload, frames=2),), {})


def test_key_is_stable_for_equal_kwargs():
    """Keyword order at the call site must not decide which cache entry is read.

    ``_default_key_function()`` hands ``kwargs`` straight to ``dumps()``, which writes a
    dict in insertion order — so two call sites passing the same arguments in a
    different order cached the same value twice.
    """
    assert _get_key(None, "ns", (), {"alpha": 1, "beta": 2}) == _get_key(
        None, "ns", (), {"beta": 2, "alpha": 1}
    )


def test_key_distinguishes_container_types():
    """Every container canonicalizes to one shape, which must still name its type."""
    keys = {
        _get_key(None, "ns", (container,), {})
        for container in ([1, 2], (1, 2), {1, 2}, frozenset({1, 2}), {1: 2})
    }

    assert len(keys) == 5


def test_key_distinguishes_container_subclasses_by_hidden_state():
    """A container subclass may mean something its contents do not show.

    ``OrderedDict`` compares by order, ``defaultdict`` by factory. A stand-in built from
    the items alone hands two unequal values one key, and a key that is wrong serves
    another call's cached value — where a key that is merely unstable misses.
    """
    assert _get_key(None, "ns", (OrderedDict([("a", 1), ("b", 2)]),), {}) != _get_key(
        None, "ns", (OrderedDict([("b", 2), ("a", 1)]),), {}
    )
    assert _get_key(None, "ns", (defaultdict(list),), {}) != _get_key(
        None, "ns", (defaultdict(set),), {}
    )


def test_key_unchanged_for_arguments_without_models():
    """Content-hash keys must keep hashing to what they always did."""
    assert _get_key(lambda: "my-key", "ns", (), {}) == CACHE_KEY_FORMAT.format(
        namespace="ns", key=sha256(dumps("my-key")).hexdigest()
    )


def test_invalidate_nonexistent_key():
    """Test invalidate returns False when key doesn't exist."""
    redis_client = get_redis_cache_client()
    redis_client.hdel.return_value = 0  # No keys deleted

    result = cache_invalidate("test.namespace", lambda x: (x,), "key123")

    assert result is False
