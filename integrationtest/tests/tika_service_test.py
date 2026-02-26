from pathlib import Path
from typing import Generator

import pytest
from common.dependencies import get_lazybytes_service
from worker.dependencies import get_tika_service
from worker.services.tika_service import TikaResult

from utils.consts import ASSETS_DIR


def yield_bytes(path: Path) -> Generator[bytes, None, None]:
    yield path.read_bytes()


class TestTikaService:

    def test_detect_empty(
        self,
    ):
        result = get_tika_service().get_file_type_from_generator((b for b in []))
        assert result == ""

    def test_detect_png_file_type(
        self,
    ):
        png = "1.png"
        result = get_tika_service().get_file_type_from_generator(
            yield_bytes(ASSETS_DIR / png)
        )
        assert result == "image/png"

    def test_detect_zip_file_type(
        self,
    ):
        archive = "archive.zip"
        result = get_tika_service().get_file_type_from_generator(
            yield_bytes(ASSETS_DIR / archive)
        )
        assert result == "application/zip"

    def test_detect_gzip_file_type(
        self,
    ):
        archive = "archive.tar.gz"
        result = get_tika_service().get_file_type_from_generator(
            yield_bytes(ASSETS_DIR / archive)
        )
        assert result == "application/gzip"

    def test_detect_eml_file_type(
        self,
    ):
        eml = "basic_email.eml"
        result = get_tika_service().get_file_type_from_generator(
            yield_bytes(ASSETS_DIR / eml)
        )
        assert result == "message/rfc822"

    def test_detect_pdf_file_type(
        self,
    ):
        pdf = "home.pdf"
        result = get_tika_service().get_file_type_from_generator(
            yield_bytes(ASSETS_DIR / pdf)
        )
        assert result == "application/pdf"

    def test_language_empty(
        self,
    ):
        result = get_tika_service().get_language_from_generator((b for b in []))
        assert result == ""

    def test_language_english_txt(
        self,
    ):
        txt = "text.txt"
        result = get_tika_service().get_language_from_generator(
            yield_bytes(ASSETS_DIR / txt)
        )
        assert result == "en"

    def test_language_german_txt(
        self,
    ):
        txt = "text_de.txt"
        result = get_tika_service().get_language_from_generator(
            yield_bytes(ASSETS_DIR / txt)
        )
        assert result == "de"

    def test_language_english_eml(
        self,
    ):
        eml = "basic_email.eml"
        result = get_tika_service().get_language_from_generator(
            yield_bytes(ASSETS_DIR / eml)
        )
        assert result == "en"

    def test_language_english_pdf(
        self,
    ):
        pdf = "home.pdf"
        result = get_tika_service().get_language_from_generator(
            yield_bytes(ASSETS_DIR / pdf)
        )
        assert result == "en"

    def test_parse_empty(
        self,
    ):
        result = get_tika_service().parse_from_generator((b for b in []))
        assert result == TikaResult()

    def test_parse_eml_attachments(
        self,
    ):
        mail = "attachment_content_disposition.eml"
        result = get_tika_service().parse_from_generator(yield_bytes(ASSETS_DIR / mail))
        assert len(result.attachments) == 1
        assert all("api.rb" == attachment.name for attachment in result.attachments)

    def test_parse_mbox_eml(
        self,
    ):
        mail = "attachment_pdf.eml"
        result = get_tika_service().parse_from_generator(yield_bytes(ASSETS_DIR / mail))
        assert len(result.attachments) == 1
        assert all("0.eml" == attachment.name for attachment in result.attachments)

    def test_parse_pst_file(
        self,
    ):
        mail = "sample.pst"
        result = get_tika_service().parse_from_generator(yield_bytes(ASSETS_DIR / mail))
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
        result = get_tika_service().parse_from_generator(
            yield_bytes(ASSETS_DIR / asset)
        )
        assert result.text
        with get_lazybytes_service().load_memoryview(result.text) as memview:
            result_text = memview.tobytes().decode()
            assert all(expected in result_text for expected in expected_identified)
