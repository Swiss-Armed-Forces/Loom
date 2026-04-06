from hashlib import sha256
from pickle import dumps, loads

from common.dependencies import get_redis_cache_client
from common.utils.cache import cache, cache_get, cache_invalidate, cache_set


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


def test_invalidate_nonexistent_key():
    """Test invalidate returns False when key doesn't exist."""
    redis_client = get_redis_cache_client()
    redis_client.hdel.return_value = 0  # No keys deleted

    result = cache_invalidate("test.namespace", lambda x: (x,), "key123")

    assert result is False
