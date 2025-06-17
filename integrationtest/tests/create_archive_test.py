import zipfile
from io import BytesIO
from uuid import UUID

import requests
from common.dependencies import get_archive_encryption_service
from common.services.query_builder import QueryParameters

from utils.consts import ARCHIVE_ENDPOINT, REQUEST_TIMEOUT
from utils.create_archive import create_archive
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_archives_from_api,
    fetch_files_from_api,
    fetch_query_id,
)
from utils.upload_asset import upload_asset, upload_many_assets


class ArchiveNotCreatedException(Exception):
    pass


def _download_archive_and_check_if_files_are_there(archive_id: UUID, files: list[str]):
    """Downloads and extracts an archive and checks if the files match the given
    list."""

    def assert_files_in_archive(content: bytes):
        # unzip archive and check if file is there
        with zipfile.ZipFile(BytesIO(content)) as zip_file:
            zip_file_namelist = zip_file.namelist()
            assert all(file_name in zip_file_namelist for file_name in files)

    # test unencrypted
    response = requests.get(
        f"{ARCHIVE_ENDPOINT}/{archive_id}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    assert_files_in_archive(response.content)

    # test encrypted
    response = requests.get(
        f"{ARCHIVE_ENDPOINT}/{archive_id}?encrypted=true",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    decrypted_archive = b""
    with get_archive_encryption_service().get_decryptor(
        BytesIO(response.content)
    ) as decryptor:
        while True:
            plaintext = decryptor()
            if plaintext == b"":
                break
            decrypted_archive += plaintext
    assert_files_in_archive(decrypted_archive)


def test_create_archive_is_listed_in_api():
    created_archive = create_archive(
        QueryParameters(search_string="*", query_id=fetch_query_id())
    )

    # Note: we don't wait for a specific state here, we expect
    # the archive to be listed immediatly after we created it.
    archives = fetch_archives_from_api(expected_state=None)
    assert len(archives) == 1
    assert created_archive.archive_id == archives[0].file_id
    # wait for acrhive to be created
    fetch_archives_from_api(expected_no_of_archives=len(archives))


def test_create_archive_is_created_correctly():
    upload_asset("basic_email.eml")
    fetch_files_from_api("*", expected_no_of_files=1)

    create_archive(QueryParameters(search_string="*", query_id=fetch_query_id()))
    archives = fetch_archives_from_api()

    assert len(archives) == 1
    assert archives[0].file_id is not None
    assert archives[0].sha256 is not None
    assert archives[0].content.size > 0


def test_if_files_contain_archive_links():
    upload_asset("basic_email.eml")
    fetch_files_from_api("*", expected_no_of_files=1)

    create_archive(QueryParameters(search_string="*", query_id=fetch_query_id()))
    archives = fetch_archives_from_api()

    fetch_files_from_api(
        search_string=f'archives:"{archives[0].file_id}"', expected_no_of_files=1
    )


def test_download_created_archive():
    upload_asset("basic_email.eml")
    fetch_files_from_api("*", expected_no_of_files=1)

    create_archive(QueryParameters(search_string="*", query_id=fetch_query_id()))
    archives = fetch_archives_from_api()

    _download_archive_and_check_if_files_are_there(
        archives[0].file_id, ["//api-upload/basic_email.eml"]
    )


def test_create_archive_with_more_than_10_files():
    asset_count = 15
    assets = ["text.txt" for _ in range(asset_count)]
    asset_file_names = [f"text_{i}.txt" for i in range(asset_count)]

    upload_many_assets(assets, asset_file_names)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    create_archive(QueryParameters(search_string="*", query_id=fetch_query_id()))
    archives = fetch_archives_from_api(
        # We have to wait here a bit longer, because the pipeline will be busy processing
        # all those files we just uploaded.
        max_wait_time_per_archive=DEFAULT_MAX_WAIT_TIME_PER_FILE
        * asset_count,
    )

    _download_archive_and_check_if_files_are_there(
        archives[0].file_id, [f"//api-upload/{f}" for f in asset_file_names]
    )


def test_create_multiple_archives_with_different_files():
    assets = [
        "basic_email.eml",
        "ocr.jpg",
        "home.pdf",
    ]
    assets_one = assets[0]

    expected_files = [f"//api-upload/{asset}" for asset in assets]
    expected_files_one = [f"//api-upload/{assets_one}"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    # create two archives
    archive_with_all_files = create_archive(
        QueryParameters(search_string="*", query_id=fetch_query_id())
    )
    archive_with_one_file = create_archive(
        QueryParameters(
            search_string=f"filename:{assets[0]}", query_id=fetch_query_id()
        )
    )

    # ensure that both archives are created
    fetch_archives_from_api(expected_no_of_archives=2)

    # download & verify
    _download_archive_and_check_if_files_are_there(
        archive_with_all_files.archive_id,
        expected_files,
    )
    _download_archive_and_check_if_files_are_there(
        archive_with_one_file.archive_id, expected_files_one
    )
