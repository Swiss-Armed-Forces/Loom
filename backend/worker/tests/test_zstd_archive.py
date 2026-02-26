import hashlib
from os import walk
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from worker.index_file.processor.extractor import archive_extractors

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
def test_zstd_archive_extraction_hash(filename: str, content_hash: str):
    zstd_processor = archive_extractors.ZstdExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        zstd_processor.extract(f, d)
        assert sum(len(filenames) for _, _, filenames in walk(d)) == 1
        inner_file = Path(d) / "0"
        assert inner_file.is_file()

        with inner_file.open("rb") as tar_f:
            assert hashlib.sha256(tar_f.read()).hexdigest() == content_hash


def test_zstd_archive_extraction_filepaths():
    processor = archive_extractors.ZstdExtractor()

    filepath = TEST_ASSETS_DIR / "empty_file.tar.zst"

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        processor.extract(f, d)

        base_path = Path(d)

        # Check that files are extracted
        extracted_files = list(base_path.rglob("*"))
        assert len(extracted_files) > 0

        # Verify no directory traversal occurred
        for extracted_file in extracted_files:
            assert extracted_file.is_relative_to(base_path)
