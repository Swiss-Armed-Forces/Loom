from common.dependencies import get_redis_cache_client
from common.utils.cache import CacheStatistics, get_cache_statistics
from fastapi import APIRouter, Depends
from redis import StrictRedis

router = APIRouter()

_redis_client = Depends(get_redis_cache_client)


@router.get("/")
def get_caching_stats(
    redis_client: StrictRedis = _redis_client,
) -> CacheStatistics:
    return get_cache_statistics(redis_client)
