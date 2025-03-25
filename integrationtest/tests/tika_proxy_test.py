from pathlib import Path

import pytest
from common.dependencies import get_lazybytes_service, get_tika_service

from utils.consts import ASSETS_DIR


def read_memoryview(path: Path):
    return memoryview(path.read_bytes())


class TestTikaProxy:

    def test_detect_png_file_type(
        self,
    ):
        png = "1.png"
        result = get_tika_service().get_file_type(read_memoryview(ASSETS_DIR / png))
        assert result == "image/png"

    def test_detect_zip_file_type(
        self,
    ):
        archive = "archive.zip"
        result = get_tika_service().get_file_type(read_memoryview(ASSETS_DIR / archive))
        assert result == "application/zip"

    def test_detect_gzip_file_type(
        self,
    ):
        archive = "archive.tar.gz"
        result = get_tika_service().get_file_type(read_memoryview(ASSETS_DIR / archive))
        assert result == "application/gzip"

    def test_detect_eml_file_type(
        self,
    ):
        eml = "basic_email.eml"
        result = get_tika_service().get_file_type(read_memoryview(ASSETS_DIR / eml))
        assert result == "message/rfc822"

    def test_detect_pdf_file_type(
        self,
    ):
        pdf = "home.pdf"
        result = get_tika_service().get_file_type(read_memoryview(ASSETS_DIR / pdf))
        assert result == "application/pdf"

    def test_parse_eml_attachments(
        self,
    ):
        mail = "attachment_content_disposition.eml"
        result = get_tika_service().parse(read_memoryview(ASSETS_DIR / mail))
        assert len(result.attachments) == 1
        assert all("api.rb" == attachment.name for attachment in result.attachments)

    def test_parse_mbox_eml(
        self,
    ):
        mail = "attachment_pdf.eml"
        result = get_tika_service().parse(read_memoryview(ASSETS_DIR / mail))
        assert len(result.attachments) == 1
        assert all("0.eml" == attachment.name for attachment in result.attachments)

    def test_parse_pst_file(
        self,
    ):
        mail = "sample.pst"
        result = get_tika_service().parse(read_memoryview(ASSETS_DIR / mail))
        # Note: we have disabled pst processing in tika
        assert len(result.attachments) == 0

    @pytest.mark.parametrize(
        "asset, expected_identified",
        [
            (
                "666666.gif",
                (
                    "kpasman",
                    "Window",
                    "Password",
                    "Ready",
                ),
            ),
            ("ocr.jpg", ("Block diagrams",)),
        ],
    )
    def test_ocr(self, asset: str, expected_identified: tuple[str]):
        result = get_tika_service().parse(read_memoryview(ASSETS_DIR / asset))
        assert result.text
        with get_lazybytes_service().load_memoryview(result.text) as memview:
            result_text = memview.tobytes().decode()
            assert all(expected in result_text for expected in expected_identified)
