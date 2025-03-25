from uuid import UUID

import requests
from api.models.query_model import QueryModel
from api.routers.index import IndexAllRequest

from utils.consts import FILES_ENDPOINT, INDEX_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api, get_file_by_name
from utils.upload_asset import upload_asset, upload_many_assets


def _reindex_file(file_id: UUID):
    response = requests.post(
        f"{FILES_ENDPOINT}/{file_id}/index/",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _reindex(query: QueryModel):
    response = requests.post(
        f"{INDEX_ENDPOINT}/",
        json=IndexAllRequest(query=query).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def test_reindex_single_file():
    asset_name = "text_de.txt"

    upload_asset(asset_name=asset_name)

    file = get_file_by_name(asset_name)

    _reindex_file(file.file_id)
    # wait for reindex
    get_file_by_name(asset_name)


def test_reindex_multiple_files():
    asset_list = ["text_de.txt", "text.txt"]

    upload_many_assets(asset_names=asset_list)
    # wait for files to be indexed
    fetch_files_from_api(search_string="*", expected_no_of_files=len(asset_list))

    _reindex(QueryModel(search_string="*"))

    # wait for re-index to finish
    fetch_files_from_api(
        search_string="*",
        expected_no_of_files=len(asset_list),
    )
