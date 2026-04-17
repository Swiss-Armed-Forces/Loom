import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from common.services.lazybytes_service import LazyBytesService

from worker.index_file.extractor.gzip_extractor import GzipExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.mark.parametrize(
    "filename,content_hash",
    [
        (
            "empty_file.txt.gz",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        (
            "empty_file.tar.gz",
            "970479b4e47382ce2da65f2a6ca1ac6e477ac8dd0b0fd5e19291d714e86d1c3a",
        ),
        (
            "home.pdf.gz",
            "7b47b4a48f9746d3e6bd4096d954ca2f50de62ed69bcf99451e4528046d69a29",
        ),
    ],
)
def test_gz_archive_extraction_hash(
    filename: str, content_hash: str, lazybytes_service_inmemory: LazyBytesService
):
    gz_processor = GzipExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        gz_processor.extract(lazy_bytes, "application/gzip", d, out_content)
        inner_file = Path(d) / "0"
        assert inner_file.is_file()

        with inner_file.open("rb") as gz_f:
            assert hashlib.sha256(gz_f.read()).hexdigest() == content_hash
