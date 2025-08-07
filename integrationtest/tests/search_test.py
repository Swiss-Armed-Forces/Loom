from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import (
    DEFAULT_MAX_WAIT_TIME_PER_FILE,
    fetch_files_from_api,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset, upload_bytes_asset, upload_many_assets


class TestCommonQueries:
    asset_list = [
        "search_test_files/confused_lorem_ipsum_search_file_test_6",
        "search_test_files/divergent_lorem_ipsum_search_file_test_7",
        "search_test_files/falsehood_lorem_ipsum_search_file_test_8",
        "search_test_files/lorem_ipsum_search_file_test_2",
        "search_test_files/maybe_lorem_ipsum_search_file_test_3",
        "search_test_files/not_lorem_ipsum_search_file_test_1",
        "search_test_files/promise_lorem_ipsum_search_file_test_5",
        "search_test_files/swear_lorem_ipsum_search_file_test_4",
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_for_all_files(self):
        # Setup the test params
        search_string = "*"
        file_count = len(self.asset_list)

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_1(self):
        # Setup the test params
        search_string = 'content:"Search test file"'
        file_count = len(self.asset_list)

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_2(self):
        # Setup the test params
        search_string = "filename, "
        file_count = 2

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_defaults_to_and(self):
        # Setup the test params
        search_string = (
            '* short_name:"falsehood_lorem_ipsum_search_file_test_8" "number 8"'
        )
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_percent(self):
        # Setup the test params
        search_string = "content:100%"
        file_count = 2

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_and(self):
        # Setup the test params
        search_string = "content:everything AND content:LIED"
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_content_for_blank_text_or(self):
        # Setup the test params
        search_string = "content:actual OR content:bro"
        file_count = 2

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_filename_for_exact_text(self):
        # Setup the test params
        search_string = "filename:swear_lorem_ipsum_search_file_test_4"
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_filename_for_wildcard_text(self):
        # Setup the test params
        search_string = "filename:divergent_*"
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_filename_for_wildcard_text_and(self):
        # Setup the test params
        search_string = "filename:(divergent_* AND *test_7)"
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_filename_for_exact_text_or(self):
        # Setup the test params
        search_string = ""
        search_string += "filename:("
        search_string += "divergent_lorem_ipsum_search_file_test_7"
        search_string += " OR "
        search_string += "falsehood_lorem_ipsum_search_file_test_8"
        search_string += ")"
        file_count = 2

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_tika_subfield_1(self):
        # Setup the test params
        search_string = 'tika_meta.Content-Encoding:"ISO-8859-1"'
        file_count = len(self.asset_list)

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_tika_subfield_2(self):
        # Setup the test params
        search_string = "tika_meta.Content-Length:52"
        file_count = 1

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_tika_subfield_3(self):
        # Setup the test params
        search_string = 'tika_meta.Content-Type:"text/plain; charset=ISO-8859-1"'
        file_count = len(self.asset_list)

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_search_tika_subfield_substring(self):
        # Setup the test params
        search_string = 'tika_meta.Content-Type:"text/plain"'
        file_count = len(self.asset_list)

        # Do the search test
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )


def test_search_for_file_name_with_quotation_mark():
    search_string = 'short_name:\\"\\"\\"text\\"\\".txt'

    upload_asset(asset_name='".zip')

    fetch_files_from_api(search_string=search_string)


def test_search_file_with_more_index_highlight_max_analyzed_offset():
    # Setup the test params
    search_string = "hello"
    with NamedTemporaryFile(mode="w+", dir=ASSETS_DIR) as tmp:
        tmp.write("hello world " * 1_000_000)
        tmp.flush()
        name = Path(tmp.name).name
        upload_asset(name)

    fetch_files_from_api(
        search_string=search_string,
        expected_no_of_files=1,
        max_wait_time_per_file=DEFAULT_MAX_WAIT_TIME_PER_FILE,
    )


def test_search_strange_chars_password():
    search_string = "p@ssw0rd"
    file_content = "This is a p@ssw0rd2023--- with strange chars"
    upload_bytes_asset(file_content.encode())

    fetch_files_from_api(search_string=search_string, expected_no_of_files=1)


class TestSearchMultilanguage:
    asset_list = [
        "search_test_files/multilanguage_file.txt",
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        # wait for assets to be processes
        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def seaerch_no_language(self):
        search_string = "house"

        file = get_file_preview_by_name(
            search_string=search_string, file_name="multilanguage_file.txt"
        )

        assert file.highlight is not None
        assert file.highlight["content"][0].count("highlight") == 2

    def search_single_language(self):
        search_string = "house"

        file = get_file_preview_by_name(
            search_string=search_string,
            languages=["de"],
            file_name="multilanguage_file.txt",
        )

        assert file.highlight is not None
        assert file.highlight["content"][0].count("highlight") == 4

    def search_multi_language(self):
        search_string = "house"

        file = get_file_preview_by_name(
            search_string=search_string,
            languages=["de", "fr"],
            file_name="multilanguage_file.txt",
        )

        assert file.highlight is not None
        assert file.highlight["content"][0].count("highlight") == 6
