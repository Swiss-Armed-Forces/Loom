import json
from uuid import UUID

import pytest
import requests
from api.routers.index import IndexAllRequest
from common.services.query_builder import QueryParameters

from utils.consts import FILES_ENDPOINT, INDEX_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    build_search_string,
    fetch_files_from_api,
    fetch_query_id,
    get_file_by_name,
)
from utils.upload_asset import upload_asset, upload_many_assets

# stacked.tar.gz nests one container per level: the gzip member stacked.tar (1) holds
# archive.zip (2), which holds file.txt (3). Reaching file.txt therefore needs exactly
# three levels of extraction, and two must stop at archive.zip.
STACKED_ASSET = "stacked.tar.gz"
STACKED_LEAF = "file.txt"
STACKED_LEAF_DEPTH = 3


def _reindex_file(file_id: UUID, additional_recursion_depth: int):
    response = requests.post(
        f"{FILES_ENDPOINT}/{file_id}/index",
        params={"additional_recursion_depth": additional_recursion_depth},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _reindex(query: QueryParameters):
    response = requests.post(
        f"{INDEX_ENDPOINT}",
        json=IndexAllRequest(query=query, additional_recursion_depth=0).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def test_reindex_single_file():
    asset_name = "text_de.txt"

    upload_asset(asset_name=asset_name)

    file = get_file_by_name(asset_name)

    _reindex_file(file.file_id, 0)
    # wait for reindex
    get_file_by_name(asset_name)


def test_reindex_multiple_files():
    asset_list = ["text_de.txt", "text.txt"]

    upload_many_assets(asset_names=asset_list)
    # wait for files to be indexed
    fetch_files_from_api(search_string="*", expected_no_of_files=len(asset_list))

    _reindex(QueryParameters(search_string="*", query_id=fetch_query_id()))

    # wait for re-index to finish
    fetch_files_from_api(
        search_string="*",
        expected_no_of_files=len(asset_list),
    )


def test_reindex_single_file_with_recursion_depth():
    upload_asset(asset_name=STACKED_ASSET)

    file = get_file_by_name(STACKED_ASSET)

    _reindex_file(file.file_id, additional_recursion_depth=STACKED_LEAF_DEPTH)

    # wait for reindex
    leaf = get_file_by_name(STACKED_LEAF)
    assert json.loads(leaf.raw).get("recursion_depth", 0) == STACKED_LEAF_DEPTH


@pytest.mark.usefixtures("disable_periodic_tasks")
def test_reindex_single_file_stops_at_the_requested_depth():
    """The depth is a ceiling, not a hint.

    A gate that compared with `>` instead of `>=` would still reach file.txt at the
    exact depth, so the boundary is only visible from the other side.
    """
    upload_asset(asset_name=STACKED_ASSET)

    file = get_file_by_name(STACKED_ASSET)

    _reindex_file(file.file_id, additional_recursion_depth=STACKED_LEAF_DEPTH - 1)

    # The last container the budget reaches is indexed...
    container = get_file_by_name("archive.zip")
    assert json.loads(container.raw).get("recursion_depth", 0) == (
        STACKED_LEAF_DEPTH - 1
    )

    # ...and nothing below it is. Waiting for an idle worker first is what makes the
    # absence a verdict rather than a race.
    fetch_files_from_api(
        search_string=build_search_string(
            search_string="*", field="short_name", field_value=STACKED_LEAF
        ),
        expected_no_of_files=0,
        wait_for_celery_idle=True,
    )
