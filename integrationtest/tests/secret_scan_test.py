import pytest

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset, upload_many_assets


class TestSecretScan:

    asset_list = [
        "secrets_test_files/test.env",
        "secrets_test_files/example_rsa_private_key",
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_testfiles(self):
        upload_many_assets(asset_names=self.asset_list)

        search_string = "*"
        file_count = len(self.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    def test_ripsecrets_match_env_file(self):
        fetch_files_from_api(
            search_string="ripsecrets_secrets.secret: "
            + '"APP_SECRET_KEY=8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a"'
        )

    def test_trufflehog_match_env_file(self):
        fetch_files_from_api(
            search_string="trufflehog_secrets.secret: "
            + '"https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"'
        )

    def test_ripsecrets_match_rsa_key(self):
        fetch_files_from_api(search_string="ripsecrets_secrets.line_number: 1")

    def test_trufflehog_match_rsa_key(self):
        fetch_files_from_api(search_string="trufflehog_secrets.line_number: 1")


def test_upoad_file_with_no_secret():
    upload_asset("text.txt")

    fetch_files_from_api(
        search_string="NOT trufflehog_secrets:* AND NOT ripsecrets_secrets:*"
    )
