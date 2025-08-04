from api.routers.files import GetFilesQuery, GetQuery

from utils.fetch_from_api import (
    fetch_files_by_query_from_api,
    fetch_files_from_api,
    fetch_query_id,
)
from utils.upload_asset import upload_asset


def test_pit_search():
    search_string = "*"
    asset_name = "text.txt"

    # New query id, query returns no results
    query_id1 = fetch_query_id(get_query=GetQuery(keep_alive="30m"))
    files_before_upload = fetch_files_by_query_from_api(
        GetFilesQuery(query_id=query_id1, search_string=search_string)
    ).files
    assert files_before_upload == []

    upload_asset(asset_name=asset_name)
    # wait for files to be indexed
    fetch_files_from_api(search_string=search_string)

    # Same old query id, query still returns no results
    files_after_upload_with_old_query_id = fetch_files_by_query_from_api(
        GetFilesQuery(query_id=query_id1, search_string=search_string)
    ).files
    assert files_after_upload_with_old_query_id == []

    # New query id, query returns results
    query_id2 = fetch_query_id()
    files_after_upload_with_new_query_id = fetch_files_by_query_from_api(
        GetFilesQuery(query_id=query_id2, search_string=search_string)
    ).files
    assert len(files_after_upload_with_new_query_id) == 1
