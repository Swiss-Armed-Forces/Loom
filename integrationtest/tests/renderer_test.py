import pytest

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets


class TestRenderer:

    asset_list = ["sample3.docx", "basic_email.eml", "favicon.svg"]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count + 2
        )

    def test_renderer_image(self):
        fetch_files_from_api(
            search_string="rendered_file.image_file_id:*", expected_no_of_files=4
        )

    def test_renderer_office_pdf(self):
        fetch_files_from_api(
            search_string="rendered_file.office_pdf_file_id:*", expected_no_of_files=5
        )

    def test_renderer_browser(self):
        fetch_files_from_api(
            search_string="rendered_file.browser_pdf_file_id:*", expected_no_of_files=1
        )
