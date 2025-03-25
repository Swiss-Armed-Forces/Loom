"""Test ZIP archive."""

from os import walk
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from zipfile import ZipFile

import pytest
from common.utils.random_file import random_file

from worker.index_file.processor.extractor import archive_extractors

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.mark.parametrize(
    "filename,file_count",
    [
        ("archive.zip", 1),
        ("empty_file.tar.gz", None),
        ("testarchive.zip", 3),
        ("testarchive_larger.zip", 6),
    ],
)
def test_zip_archive_extraction_count(filename: str, file_count: int | None):
    processor = archive_extractors.ZipExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        try:
            processor.extract(f, d)
            assert sum(len(files) for _, _, files in walk(d)) == file_count
        except archive_extractors.ExtractNotSupported:
            assert file_count is None


def test_zip_archive_extraction_filepaths():
    processor = archive_extractors.ZipExtractor()

    filepath = TEST_ASSETS_DIR / "testarchive_larger.zip"

    with TemporaryDirectory() as d:
        processor.extract(str(filepath), d)

        assert set(
            Path(dirpath, filename).relative_to(d)
            for dirpath, _, filenames in walk(d)
            for filename in filenames
        ) == set(
            [
                Path("morestuff/onemore/pdf-annotated.tex"),
                Path("morestuff/onemore/python.png"),
                Path("morestuff/home.pdf"),
                Path("testarchive/emptyfile.ignore"),
                Path("testarchive/testfile01.txt"),
                Path("testarchive/testfile02.txt"),
            ]
        )


def test_zip_archive_extraction_traversal():
    processor = archive_extractors.ZipExtractor()

    # evil.zip contains:
    #   - an empty file at ../emptyfile_relative
    #   - an empty file at /tmp/emptyfile_absolute
    filepath = TEST_ASSETS_DIR / "evil.zip"

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        outdir = Path(d) / "out"
        outdir.mkdir()

        processor.extract(f, outdir)

        assert not (Path(d) / "emptyfile_relative").exists()
        assert (outdir / "emptyfile_relative").read_text() == ""

        assert not Path("/tmp/emptyfile_absolute").exists()
        assert (outdir / "tmp" / "emptyfile_absolute").read_text() == ""


@pytest.mark.parametrize("random_file_size", [1 << 30, 2 << 30])
@pytest.mark.limit_memory("2 MB")
def test_zip_archive_extraction_single_file(random_file_size, tmp_path):
    with TemporaryFile(dir=tmp_path) as zip_file:
        with ZipFile(zip_file, "w") as archive:
            with random_file(tmp_path, random_file_size) as fd:
                archive.write(fd.name, "random_file")

        zip_file.flush()
        zip_file.seek(0)

        processor = archive_extractors.ZipExtractor()
        processor.extract(zip_file, tmp_path)

        filepath = tmp_path / "random_file"
        assert filepath.is_file()
        assert filepath.stat().st_size != 0
