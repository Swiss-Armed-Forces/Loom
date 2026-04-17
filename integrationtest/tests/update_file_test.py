from uuid import UUID

import pytest
import requests
from api.routers.archives import UpdateArchiveModel
from api.routers.files import UpdateFilesRequest
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest

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


def _update_file(file_id: UUID, update: UpdateFileRequest):
    """Update a single file by ID."""
    response = requests.put(
        f"{FILES_ENDPOINT}/{file_id}",
        json=update.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _update_files(update_files_request: UpdateFilesRequest):
    """Update multiple files matching a query."""
    response = requests.put(
        f"{FILES_ENDPOINT}",
        json=update_files_request.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


@pytest.mark.parametrize(
    "field_name",
    [
        "flagged",
        "seen",
    ],
)
def test_update_single_file(field_name: str):
    """Test updating a single file's hidden, flagged or seen state."""
    asset_name = "basic_email.eml"
    upload_asset(asset_name)

    # Verify initial state
    file = get_file_preview_by_name(asset_name)
    assert getattr(file, field_name) is False

    # Update the field
    update_request = UpdateFileRequest(**{field_name: True})
    _update_file(file.file_id, update_request)

    # Should find it when explicitly searching for the field
    fetch_files_from_api(
        search_string=f'full_name:"{asset_name}" AND {field_name}:true',
        expected_no_of_files=1,
    )


def test_hide_single_file():
    field_name = "hidden"
    asset_name = "basic_email.eml"
    upload_asset(asset_name)

    # Verify initial state
    file = get_file_preview_by_name(asset_name)
    assert getattr(file, field_name) is False

    # Update the field
    update_request = UpdateFileRequest(**{field_name: True})
    _update_file(file.file_id, update_request)

    # Should not find it in default search
    fetch_files_from_api(
        search_string=f'full_name:"{asset_name}"',
        expected_no_of_files=0,
        wait_for_celery_idle=True,
        allow_more_files=True,
    )

    # Should find it when explicitly searching for the field
    fetch_files_from_api(
        search_string=f'full_name:"{asset_name}" AND {field_name}:true',
        expected_no_of_files=1,
    )


@pytest.mark.parametrize(
    "field_name",
    ["hidden", "flagged", "seen"],
)
def test_update_multiple_files(field_name: str):
    """Test updating multiple files' hidden, flagged or seen state."""
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    # Update all files
    update_request = UpdateFilesRequest(
        query=QueryParameters(search_string="*", query_id=fetch_query_id()),
        request=UpdateFileRequest(**{field_name: True}),
    )
    _update_files(update_request)

    # Verify all files are updated
    fetch_files_from_api(f"{field_name}:true", expected_no_of_files=len(assets))


@pytest.mark.parametrize(
    "field_name",
    ["hidden", "flagged", "seen"],
)
def test_toggle_file_state(field_name: str):
    """Test toggling a file's hidden, flagged or seen state on and off."""
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    # Set field to True
    update_request = UpdateFilesRequest(
        query=QueryParameters(search_string="*", query_id=fetch_query_id()),
        request=UpdateFileRequest(**{field_name: True}),
    )
    _update_files(update_request)
    fetch_files_from_api(f"* AND {field_name}:true", expected_no_of_files=len(assets))

    # Set field back to False
    update_request = UpdateFilesRequest(
        query=QueryParameters(
            search_string=f"{field_name}:true", query_id=fetch_query_id()
        ),
        request=UpdateFileRequest(**{field_name: False}),
    )
    _update_files(update_request)

    # Verify all files are visible again
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
