from hashlib import sha256
from pickle import dumps

from common.dependencies import get_redis_client
from common.utils.cache import cache


@cache(key_function=lambda: "my-key")
def cached_function() -> str:
    return "testresult"


def test_cache_decorator():
    redis_client = get_redis_client()
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
