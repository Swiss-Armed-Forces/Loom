from pathlib import Path

import pytest
import requests
from api.routers.files import AddTagsRequest
from pydantic import BaseModel
from worker.index_file.tasks.auto_tag_file import AUTO_TAG_PREFIX
from worker.settings import settings

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import fetch_files_from_api, get_file_preview_by_name
from utils.upload_asset import upload_asset, upload_many_assets

NET_TAG = "net"
WEB_TAG = "web"

AUTO_TAG_FOLDER = Path("auto_tag_files")


class FileTag(BaseModel):
    filename: str
    tag: str


class TestAutoTag:
    base_asset_list = [
        FileTag(filename="net1.txt", tag=NET_TAG),
        FileTag(filename="web1.txt", tag=WEB_TAG),
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_files(self):
        file_paths = [AUTO_TAG_FOLDER / file.filename for file in self.base_asset_list]
        upload_many_assets(asset_names=[str(path) for path in file_paths])

        # wait for assets to be processed
        search_string = "*"
        file_count = len(self.base_asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

        for filetag in self.base_asset_list:
            file = get_file_preview_by_name(filetag.filename)
            tag = filetag.tag

            # manually tag the file
            response = requests.post(
                f"{FILES_ENDPOINT}/{str(file.file_id)}/tags",
                json=AddTagsRequest(tags=[tag]).model_dump(),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            # wait for tag to be set
            get_file_preview_by_name(
                filetag.filename,
                wait_for_celery_idle=True,
                checker=lambda f, tag=tag: f.tags == [tag],
            )

    single_auto_tag_data = [
        FileTag(filename="net2.txt", tag=AUTO_TAG_PREFIX + NET_TAG),
        FileTag(filename="web2.txt", tag=AUTO_TAG_PREFIX + WEB_TAG),
    ]

    @pytest.mark.parametrize("filetag", single_auto_tag_data)
    def test_single_auto_tag(self, filetag: FileTag):
        upload_asset(str(AUTO_TAG_FOLDER / filetag.filename))

        index_file = get_file_preview_by_name(filetag.filename)

        if settings.skip_auto_tag_file_while_indexing:
            assert True
        else:
            assert len(index_file.tags) == 1
            assert index_file.tags[0] == filetag.tag

    def test_multiple_auto_tag(self):
        filename = "web_net.txt"
        upload_asset(str(AUTO_TAG_FOLDER / filename))

        index_file = get_file_preview_by_name(filename)

        if settings.skip_auto_tag_file_while_indexing:
            assert True
        else:
            assert len(index_file.tags) == 2
            assert AUTO_TAG_PREFIX + NET_TAG in index_file.tags
            assert AUTO_TAG_PREFIX + WEB_TAG in index_file.tags

    def test_no_auto_tag(self):
        filename = "no_tag.txt"
        upload_asset(str(AUTO_TAG_FOLDER / filename))

        index_file = get_file_preview_by_name(filename)

        if settings.skip_auto_tag_file_while_indexing:
            assert True
        else:
            assert len(index_file.tags) == 0
