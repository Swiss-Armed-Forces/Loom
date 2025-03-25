"""Test PST archive."""

import os
import tempfile
from pathlib import Path

import pytest

from worker.index_file.processor.extractor import archive_extractors
from worker.index_file.processor.extractor.archive_extractors import PcapExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


def test_pcap_archive_extraction_files():
    test_asset = TEST_ASSETS_DIR / "http.pcap"

    processor = PcapExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)
        assert sum(len(filenames) for _, _, filenames in os.walk(d)) == 1


def test_pcap_archive_extraction_unsupported():
    test_asset = TEST_ASSETS_DIR / "evil.zip"

    processor = PcapExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        with pytest.raises(archive_extractors.ExtractNotSupported):
            processor.extract(f, d)
