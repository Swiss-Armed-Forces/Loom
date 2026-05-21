from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset


def test_deduplication():
    search_string = "*"
    asset_name = "text.txt"

    # upload the same asset twice
    upload_asset(asset_name=asset_name)

    # wait for first file to be visible
    fetch_files_from_api(
        search_string=search_string, expected_no_of_files=1, expected_state=None
    )

    upload_asset(asset_name=asset_name)

    # wait for files to be indexed (should only be 1 because of deduplication)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=1)
