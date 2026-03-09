from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from common.services.lazybytes_service import LazyBytesService

from worker.index_file.extractor.zip_extractor import ZipExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


def test_zip_archive_extraction_traversal(lazybytes_service_inmemory: LazyBytesService):
    processor = ZipExtractor()

    # evil.zip contains:
    #   - an empty file at ../emptyfile_relative
    #   - an empty file at /tmp/emptyfile_absolute
    filepath = TEST_ASSETS_DIR / "evil.zip"

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        outdir = Path(d) / "out"
        outdir.mkdir()

        processor.extract(lazy_bytes, "application/zip", str(outdir), out_content)

        assert not (Path(d) / "emptyfile_relative").exists()
        assert (outdir / "emptyfile_relative").read_text() == ""

        assert not Path("/tmp/emptyfile_absolute").exists()
        assert (outdir / "tmp" / "emptyfile_absolute").read_text() == ""
