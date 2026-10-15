import pytest

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_many_assets


class TestRenderer:

    asset_list = ["sample3.docx", "basic_email.eml", "favicon.svg"]

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def setup_testfiles(cls):
        upload_many_assets(asset_names=cls.asset_list)

        search_string = "*"
        file_count = len(cls.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count + 2
        )

    def test_renderer_image(self):
        # The email is absent here: its PDF preview replaces the image.
        fetch_files_from_api(
            search_string="rendered_file.image_data.service_id:*",
            expected_no_of_files=3,
        )

    def test_renderer_office_pdf(self):
        # The email is absent here: its PDF comes from chromium and is kept as-is.
        fetch_files_from_api(
            search_string="rendered_file.office_pdf_data.service_id:*",
            expected_no_of_files=4,
        )

    def test_renderer_browser(self):
        # The svg, and the email rendered as one continuous page.
        fetch_files_from_api(
            search_string="rendered_file.browser_pdf_data.service_id:*",
            expected_no_of_files=2,
        )
