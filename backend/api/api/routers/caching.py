from common.dependencies import get_redis_client
from common.utils.cache import CACHE_KEY_FORMAT, CACHE_KEY_PREFIX
from fastapi import APIRouter, Depends
from redis import StrictRedis

from api.models.statistics_model import CacheStatistics, CacheStatisticsEntryModel

router = APIRouter()

_redis_client = Depends(get_redis_client)


@router.get("/")
def get_caching_stats(
    redis_client: StrictRedis = _redis_client,
) -> CacheStatistics:
    result: CacheStatistics = CacheStatistics()

    # need to do utf-8 decode here as we have set decode_responses=False
    # for StrictRedis due to pickled binaries which cause errors otherwise
    keys = redis_client.keys(f"{{{CACHE_KEY_PREFIX}*[miss|hits]?")
    keys = list(map(lambda key: key.decode(), keys))

    tasks = list(map(lambda key: key.split(":")[1][:-1], keys))
    for task in set(tasks):
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
            mem_size=int(mem_size),
            entries_count=int(entries_count),
            hits_count=int(hits_count if hits_count else 0),
            miss_count=int(miss_count if miss_count else 0),
        )

    return result
