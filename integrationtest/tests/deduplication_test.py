from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset


def test_deduplication():
    search_string = "*"
    asset_name = "text.txt"

    # upload the same asset twice
    file1 = upload_asset(asset_name=asset_name)
    file2 = upload_asset(asset_name=asset_name)

    # check if was deduplicated
    assert file1.file_id == file2.file_id
    # wait for files to be indexed (should only be just 1 becaue of deduplication)
    fetch_files_from_api(search_string=search_string, expected_no_of_files=1)
