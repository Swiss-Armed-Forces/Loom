import platform

import pytest

from utils.fetch_from_api import fetch_files_from_api
from utils.upload_asset import upload_asset, upload_many_assets

# ripsecrets publishes no linux/arm64 release artifact, so the worker image does
# not ship the binary there and ripsecrets_scan_task reports "not scanned" for
# every file. The cluster runs the host architecture (up.sh builds for
# linux/${TARGETARCH}), so the host machine tells us whether to expect results.
# See the "ARM64 feature gaps" section in Documentation/installation.md.
ripsecrets_available = pytest.mark.skipif(
    platform.machine() not in ("x86_64", "amd64"),
    reason="ripsecrets is not available on this architecture",
)


class TestSecretScan:

    asset_list = [
        "secrets_test_files/test.env",
        "secrets_test_files/example_rsa_private_key",
    ]

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def setup_testfiles(cls):
        upload_many_assets(asset_names=cls.asset_list)

        search_string = "*"
        file_count = len(cls.asset_list)
        fetch_files_from_api(
            search_string=search_string, expected_no_of_files=file_count
        )

    @ripsecrets_available
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

    @ripsecrets_available
    def test_ripsecrets_match_rsa_key(self):
        fetch_files_from_api(search_string="ripsecrets_secrets.line_number: 1")

    def test_trufflehog_match_rsa_key(self):
        fetch_files_from_api(search_string="trufflehog_secrets.line_number: 1")


def test_upload_file_with_no_secret():
    upload_asset("text.txt")

    # The ripsecrets clause is trivially satisfied where ripsecrets is absent;
    # the trufflehog clause carries the assertion on every architecture.
    fetch_files_from_api(
        search_string="NOT trufflehog_secrets:* AND NOT ripsecrets_secrets:*"
    )
