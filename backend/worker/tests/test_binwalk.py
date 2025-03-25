import tempfile
from os import listdir
from pathlib import Path

from worker.index_file.processor.extractor.archive_extractors import BinwalkExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


def test_binwalk_extraction_files():
    test_asset = TEST_ASSETS_DIR / "single_file.tar.gz"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)
        assert len(listdir(d)) != 0


def test_binwalk_extraction_files_stdout_file_exists():
    test_asset = TEST_ASSETS_DIR / "single_file.tar.gz"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)
        stdout_file_path = Path(d, TEST_ASSETS_DIR)
        assert stdout_file_path.exists()


def test_binwalk_extraction_files_directory_not_exist():
    test_asset = TEST_ASSETS_DIR / "actually_text.wav"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)
        assert len(listdir(d)) == 0
