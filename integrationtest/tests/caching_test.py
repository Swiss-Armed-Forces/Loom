from http.client import REQUEST_TIMEOUT

import requests
from common.utils.cache import CacheStatistics

from utils.consts import CACHING_ENDPOINT
from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset


def _get_stats() -> CacheStatistics:
    response = requests.get(
        f"{CACHING_ENDPOINT}/",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return CacheStatistics.model_validate(response.json())


def test_caching():
    search_string = "*"
    asset_name = "text.txt"

    upload_asset(asset_name=asset_name)
    # wait for files to be indexed
    fetch_files_from_api(search_string=search_string, expected_no_of_files=1)

    caching_results_1 = _get_stats()
    assert caching_results_1.mem_size_total == 15368
    assert caching_results_1.entries_count_total == 21
    assert caching_results_1.hits_count_total == 25
    assert caching_results_1.miss_count_total == 21

    upload_asset(asset_name=asset_name, upload_file_name="text2.txt")
    # wait for files to be indexed
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)

    caching_results_2 = _get_stats()
    assert caching_results_2.mem_size_total == 18592
    assert caching_results_2.entries_count_total == 22
    assert caching_results_2.hits_count_total == 70  # more hits (nice)!
    assert caching_results_2.miss_count_total == 22
