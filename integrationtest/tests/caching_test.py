from http.client import REQUEST_TIMEOUT

import requests
from api.models.statistics_model import CacheStatistics

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

    caching_results = _get_stats()
    assert caching_results.mem_size_total == 2000
    assert caching_results.entries_count_total == 3
    assert caching_results.hits_count_total == 0
    assert caching_results.miss_count_total == 3

    upload_asset(asset_name=asset_name, upload_file_name="text2.txt")
    # wait for files to be indexed
    fetch_files_from_api(search_string=search_string, expected_no_of_files=2)

    caching_results = _get_stats()
    assert caching_results.mem_size_total == 2000
    assert caching_results.entries_count_total == 3
    assert caching_results.hits_count_total == 3  # more hits!
    assert caching_results.miss_count_total == 3
