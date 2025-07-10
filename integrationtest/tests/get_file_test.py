import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

import pytest
from api.routers.files import CONTENT_PREVIEW_LENGTH
from pydantic import BaseModel
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE

from utils.consts import ASSETS_DIR, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_by_name,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset

logger = logging.getLogger(__name__)


class FileInfo(BaseModel):
    id: UUID
    name: str


class TestGetShortFile:

    @pytest.fixture(scope="class")
    def file_info(self) -> FileInfo:
        asset = "text.txt"
        upload_file_response = upload_asset(asset)

        # wait for assets to be processes
        search_string = "*"
        file_count = 1
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )
        return FileInfo(
            name=asset,
            id=upload_file_response.file_id,
        )

    def test_get_file(self, file_info: FileInfo):
        actual = get_file_by_name(file_info.name)

        assert actual.file_id == file_info.id
        assert actual.content == "Dummy Text\n"
        assert actual.name == "text.txt"

    def test_get_file_highlight_text(self, file_info: FileInfo):
        search_string = "Dummy"
        actual = get_file_by_name(file_info.name, search_string)

        assert actual.file_id == file_info.id
        assert actual.highlight == {
            "content": [f"<highlight>{search_string}</highlight> Text\n"],
            "short_name": [f"<highlight>{file_info.name}</highlight>"],
        }

    def test_get_file_preview(self, file_info: FileInfo):
        actual = get_file_preview_by_name(file_info.name)

        assert actual.file_id == file_info.id
        assert actual.content == "Dummy Text\n"
        assert actual.content_is_truncated is False
        assert actual.name == "text.txt"

    def test_get_file_preview_highlight_text(self, file_info: FileInfo):
        search_string = "Dummy"
        actual = get_file_preview_by_name(file_info.name, search_string)

        assert actual.file_id == file_info.id
        assert actual.highlight == {
            "content": [f"<highlight>{search_string}</highlight> Text"],
            "short_name": [f"<highlight>{file_info.name}</highlight>"],
        }


class TestGetLongFile:
    @pytest.fixture(scope="class")
    def file_info(self) -> FileInfo:
        with NamedTemporaryFile(mode="w+", dir=ASSETS_DIR) as tmp:
            tmp.write("a" * (TIKA_MAX_TEXT_SIZE + 1))
            tmp.flush()
            file_name = Path(tmp.name).name
            file_upload_response = upload_asset(
                file_name, request_timeout=REQUEST_TIMEOUT * 10
            )

        search_string = "*"
        file_count = 1
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )
        return FileInfo(
            name=file_name,
            id=file_upload_response.file_id,
        )

    def test_get_file_preview_truncate_text(self, file_info: FileInfo):
        actual = get_file_preview_by_name(file_info.name)

        assert actual.file_id == file_info.id
        assert actual.content_preview_is_truncated
        assert len(actual.content) <= CONTENT_PREVIEW_LENGTH

    def test_get_file_truncate_text(self, file_info: FileInfo):
        actual = get_file_by_name(
            file_info.name, max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE * 2
        )

        assert actual.file_id == file_info.id
        assert len(actual.content) <= TIKA_MAX_TEXT_SIZE
