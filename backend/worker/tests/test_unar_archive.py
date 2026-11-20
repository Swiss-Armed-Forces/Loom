from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from common.services.lazybytes_service import InMemoryTempLazyBytesService

from worker.index_file.extractor.unar_extractor import UnarExtractor

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


def test_unar_archive_extraction_traversal(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    processor = UnarExtractor()

    # evil.rar contains:
    #   - an empty file at ../emptyfile_relative
    #   - an empty file at /tmp/emptyfile_absolute
    # unar keeps both inside the output directory, rewriting '..' to a literal
    # '__Parent__' segment and dropping the leading slash.
    filepath = TEST_ASSETS_DIR / "evil.rar"

    with TemporaryDirectory() as d, filepath.open(
        "rb"
    ) as f, NamedTemporaryFile() as out_content:
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        outdir = Path(d) / "out"
        outdir.mkdir()

        processor.extract(lazy_bytes, "application/vnd.rar", str(outdir), out_content)

        assert not (Path(d) / "emptyfile_relative").exists()
        assert (outdir / "__Parent__" / "emptyfile_relative").read_text() == ""

        assert not Path("/tmp/emptyfile_absolute").exists()
        assert (outdir / "tmp" / "emptyfile_absolute").read_text() == ""
