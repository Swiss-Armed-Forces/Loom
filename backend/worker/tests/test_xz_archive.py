import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from common.services.lazybytes_service import LazyBytesService

from worker.index_file.extractor.xz_extractor import XZExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.mark.parametrize(
    "filename,content_hash",
    [
        (
            "empty_file.txt.xz",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        (
            "empty_file.tar.xz",
            "7b1752b20d33415cfc8aed628283f00d0bcf4e3640b981e4845aef2446db775e",
        ),
        (
            "home.pdf.xz",
            "7b47b4a48f9746d3e6bd4096d954ca2f50de62ed69bcf99451e4528046d69a29",
        ),
    ],
)
def test_xz_archive_extraction_hash(
    filename: str, content_hash: str, lazybytes_service_inmemory: LazyBytesService
):
    xz_processor = XZExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        xz_processor.extract(lazy_bytes, "application/x-xz", d, out_content)
        inner_file = Path(d) / "0"
        assert inner_file.is_file()

        with inner_file.open("rb") as tar_f:
            assert hashlib.sha256(tar_f.read()).hexdigest() == content_hash
