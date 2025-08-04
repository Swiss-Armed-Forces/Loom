from uuid import UUID

import requests
from api.routers.archives import UpdateArchiveModel
from api.routers.files import UpdateFileRequest, UpdateFilesRequest
from common.services.query_builder import QueryParameters

from utils.consts import ARCHIVE_ENDPOINT, FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.create_archive import create_archive
from utils.fetch_from_api import (
    fetch_archives_from_api,
    fetch_files_from_api,
    fetch_query_id,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset, upload_many_assets


def _hide_archive(archive_id: UUID):
    response = requests.post(
        f"{ARCHIVE_ENDPOINT}/{archive_id}",
        json=UpdateArchiveModel(hidden=True).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _update_file(file_id: str, update: UpdateFileRequest):
    response = requests.put(
        f"{FILES_ENDPOINT}/{file_id}",
        json=update.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _update_files(update_files_request: UpdateFilesRequest):
    response = requests.put(
        f"{FILES_ENDPOINT}",
        json=update_files_request.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def test_hide_file():
    asset_name = "basic_email.eml"
    upload_asset(asset_name)

    # should not be hidden: we can search for it
    file = get_file_preview_by_name(asset_name)
    assert file.hidden is False

    # hide file
    _update_file(str(file.file_id), UpdateFileRequest(hidden=True))

    # we should not find it when we don't specify hidden files
    fetch_files_from_api(
        search_string=f'full_name:"{asset_name}"', expected_no_of_files=0
    )

    # but we should find it when we search for hidden files
    fetch_files_from_api(
        search_string=f'full_name:"{asset_name}" AND hidden:true',
        expected_no_of_files=1,
    )


def test_hide_files():
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    hide_files_request = UpdateFilesRequest(
        query=QueryParameters(search_string="*", query_id=fetch_query_id()), hidden=True
    )

    _update_files(hide_files_request)

    fetch_files_from_api("hidden:true", expected_no_of_files=len(assets))


def test_hide_unhide_files():
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    hide_files_request = UpdateFilesRequest(
        query=QueryParameters(search_string="*", query_id=fetch_query_id()), hidden=True
    )
    _update_files(hide_files_request)
    fetch_files_from_api("* AND hidden:true", expected_no_of_files=len(assets))

    hide_files_request = UpdateFilesRequest(
        query=QueryParameters(search_string="hidden:true", query_id=fetch_query_id()),
        hidden=False,
    )
    _update_files(hide_files_request)

    fetch_files_from_api("*", expected_no_of_files=len(assets))


def test_hide_archive():
    created_archive = create_archive(
        QueryParameters(search_string="*", query_id=fetch_query_id())
    )

    # Note: we don't wait for a specific state here, we expect
    # the archive to be listed immediately after we created it.
    archives = fetch_archives_from_api(expected_no_of_archives=1, expected_state=None)
    assert len(archives) == 1
    assert created_archive.archive_id == archives[0].file_id

    # hide it
    _hide_archive(created_archive.archive_id)

    # assertions
    archives = fetch_archives_from_api(expected_no_of_archives=0, expected_state=None)
    assert len(archives) == 0
