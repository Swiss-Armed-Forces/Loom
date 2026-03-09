from pathlib import Path
from tarfile import OutsideDestinationError
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
from common.services.lazybytes_service import LazyBytesService

from worker.index_file.extractor.base import ExtractNotSupported
from worker.index_file.extractor.tar_extractor import TarExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


def test_tar_archive_extraction_traversal(lazybytes_service_inmemory: LazyBytesService):
    processor = TarExtractor()

    # evil.tar only has one file at ../emptyfile
    filepath = TEST_ASSETS_DIR / "evil.tar"

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        with pytest.raises(ExtractNotSupported) as exc_info:
            processor.extract(lazy_bytes, "application/x-tar", d, out_content)
        assert isinstance(exc_info.value.__cause__, OutsideDestinationError)
