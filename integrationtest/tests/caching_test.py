from http.client import REQUEST_TIMEOUT

import pytest
import requests
from common.utils.cache import CacheStatistics
from pydantic import BaseModel

from utils.consts import CACHING_ENDPOINT
from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset

pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")


def _get_stats() -> CacheStatistics:
    response = requests.get(
        f"{CACHING_ENDPOINT}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return CacheStatistics.model_validate(response.json())


class CacheStatsTotal(BaseModel):
    mem_size_total: int
    entries_count_total: int
    miss_count_total: int
    hits_count_total: int


def calc_totals(stats: CacheStatistics) -> CacheStatsTotal:
    size = 0
    miss = 0
    hits = 0
    count = 0
    for x in stats.root.keys():
        if x.split(".")[0] != "worker":
            continue

        size += stats.root[x].mem_size
        miss += stats.root[x].miss_count
        hits += stats.root[x].hits_count
        count += stats.root[x].entries_count

    return CacheStatsTotal(
        mem_size_total=size,
        entries_count_total=count,
        miss_count_total=miss,
        hits_count_total=hits,
    )


# Flaky: 1/1000 fails due to race/sync issue.
# https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/work_items/255
@pytest.mark.flaky(reruns=3)
def test_caching():
    search_string = "*"
    asset_name = "text.txt"

    upload_asset(asset_name=asset_name)
    # wait for files to be indexed and all pipeline tasks to complete
    fetch_files_from_api(
        search_string=search_string,
        expected_no_of_files=1,
        wait_for_celery_idle=True,
    )

    caching_results_1 = _get_stats()

    stats_1 = calc_totals(caching_results_1)

    assert stats_1.mem_size_total > 0
    assert stats_1.entries_count_total > 0
    assert stats_1.hits_count_total > 0
    assert stats_1.miss_count_total > 0

    upload_asset(asset_name=asset_name, upload_file_name="text2.txt")
    # wait for files to be indexed and all pipeline tasks to complete
    fetch_files_from_api(
        search_string=search_string,
        expected_no_of_files=2,
        wait_for_celery_idle=True,
    )

    caching_results_2 = _get_stats()

    stats_2 = calc_totals(caching_results_2)

    assert stats_2.mem_size_total == stats_1.mem_size_total
    assert stats_2.entries_count_total == stats_1.entries_count_total
    assert stats_2.miss_count_total == stats_1.miss_count_total
    assert stats_2.hits_count_total > stats_1.hits_count_total
