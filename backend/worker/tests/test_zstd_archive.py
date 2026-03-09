import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from common.services.lazybytes_service import LazyBytesService

from worker.index_file.extractor.zstd_extractor import ZstdExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.mark.parametrize(
    "filename,content_hash",
    [
        (
            "empty_file.tar.zst",
            "28d5fcd93ec3a903716510eb9a542cd0cab37917f2005ad2f498d038bab77d2d",
        ),
        (
            "python.png.zst",
            "ccb38978f900ce7033a404ddf4d848fbcc14a96b74ae682ff80e331342aba9fb",
        ),
        (
            "topsecret.pdf.zst",
            "164fc03ac93077ae20ca87c0e6f6f834973cdc80a4ef047fd9338103d352e796",
        ),
    ],
)
def test_zstd_archive_extraction_hash(
    filename: str, content_hash: str, lazybytes_service_inmemory: LazyBytesService
):
    zstd_processor = ZstdExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        zstd_processor.extract(lazy_bytes, "application/zstd", d, out_content)
        inner_file = Path(d) / "0"
        assert inner_file.is_file()

        with inner_file.open("rb") as tar_f:
            assert hashlib.sha256(tar_f.read()).hexdigest() == content_hash
