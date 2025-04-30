from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from api.routers.files import CONTENT_PREVIEW_LENGTH, FileUploadResponse
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_by_name,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset


class TestGetShortFile:

    asset = "text.txt"

    @pytest.fixture(scope="class")
    def upload_file_response(self) -> FileUploadResponse:
        upload_file_response = upload_asset(self.asset)

        # wait for assets to be processes
        search_string = "*"
        file_count = 1
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )
        return upload_file_response

    def test_get_file(self, upload_file_response: FileUploadResponse):
        actual = get_file_by_name(self.asset)

        assert actual.file_id == upload_file_response.file_id
        assert actual.content == "Dummy Text\n"
        assert actual.name == "text.txt"

    def test_get_file_highlight_text(self, upload_file_response: FileUploadResponse):
        search_string = "Dummy"
        actual = get_file_by_name(self.asset, search_string)

        assert actual.file_id == upload_file_response.file_id
        assert actual.highlight == {
            "content": [f"<highlight>{search_string}</highlight> Text"],
            "short_name": [f"<highlight>{self.asset}</highlight>"],
        }

    def test_get_file_preview(self, upload_file_response: FileUploadResponse):
        actual = get_file_preview_by_name(self.asset)

        assert actual.file_id == upload_file_response.file_id
        assert actual.content == "Dummy Text\n"
        assert actual.content_is_truncated is False
        assert actual.name == "text.txt"

    def test_get_file_preview_highlight_text(
        self, upload_file_response: FileUploadResponse
    ):
        search_string = "Dummy"
        actual = get_file_preview_by_name(self.asset, search_string)

        assert actual.file_id == upload_file_response.file_id
        assert actual.highlight == {
            "content": [f"<highlight>{search_string}</highlight> Text"],
            "short_name": [f"<highlight>{self.asset}</highlight>"],
        }


class TestGetLongFile:
    filename = ""

    @pytest.fixture(scope="class")
    def upload_file_response(self) -> FileUploadResponse:
        with NamedTemporaryFile(mode="w+", dir=ASSETS_DIR) as tmp:
            tmp.write("a" * (TIKA_MAX_TEXT_SIZE + 1))
            tmp.flush()
            self.filename = Path(tmp.name).name
            upload_file_response = upload_asset(self.filename)

        search_string = "*"
        file_count = 1
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )
        return upload_file_response

    @pytest.mark.skip(reason="Flaky test")
    def test_get_file_preview_truncate_text(
        self, upload_file_response: FileUploadResponse
    ):
        actual = get_file_preview_by_name(self.filename)

        assert actual.file_id == upload_file_response.file_id
        assert actual.content_preview_is_truncated
        assert len(actual.content) <= CONTENT_PREVIEW_LENGTH

    @pytest.mark.skip(reason="Flaky test")
    def test_get_file_truncate_text(self, upload_file_response: FileUploadResponse):
        actual = get_file_by_name(
            self.filename, max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE * 2
        )

        assert actual.file_id == upload_file_response.file_id
        assert len(actual.content) <= TIKA_MAX_TEXT_SIZE
