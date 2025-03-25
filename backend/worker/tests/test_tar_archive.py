"""Test TAR archive."""

import tarfile
from os import walk
from pathlib import Path
from tarfile import OutsideDestinationError
from tempfile import TemporaryDirectory, TemporaryFile

import pytest
from common.utils.random_file import random_file

from worker.index_file.processor.extractor import archive_extractors

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.mark.parametrize(
    "filename,file_count",
    [
        ("empty_file.tar", 1),
        ("empty_file.tar.gz", 1),
        ("hidden_file.tar", 1),
        ("hidden_file.tar.gz", 1),
        ("multi_file.tar", 3),
        ("multi_file.tar.gz", 3),
        ("sub_folder.tar", 2),
        ("sub_folder.tar.gz", 2),
        ("sub_sub_folder.tar", 3),
        ("sub_sub_folder.tar.gz", 3),
        ("pdf-annotated.pdf", None),
        ("testarchive.zip", None),
    ],
)
def test_tar_archive_extraction_count(filename: str, file_count: int | None):
    processor = archive_extractors.TarExtractor()

    filepath = TEST_ASSETS_DIR / filename

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        try:
            processor.extract(f, d)
            assert sum(len(filenames) for _, _, filenames in walk(d)) == file_count
        except archive_extractors.ExtractNotSupported:
            assert file_count is None


def test_tar_archive_extraction_filepaths():
    processor = archive_extractors.TarExtractor()

    filepath = TEST_ASSETS_DIR / "sub_sub_folder.tar"

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        processor.extract(f, d)

        assert set(
            Path(dirpath, filename).relative_to(d)
            for dirpath, _, filenames in walk(d)
            for filename in filenames
        ) == set(
            [
                Path("sub_sub_folder_top_tar/sub_sub_folder_bot_tar/child_file_tar"),
                Path("sub_sub_folder_top_tar/middle_file_tar"),
                Path("super_parent_file_tar"),
            ]
        )


def test_tar_archive_extraction_traversal():
    processor = archive_extractors.TarExtractor()

    # evil.tar only has one file at ../emptyfile
    filepath = TEST_ASSETS_DIR / "evil.tar"

    with TemporaryDirectory() as d, filepath.open("rb") as f:
        with pytest.raises(archive_extractors.ExtractNotSupported) as exc_info:
            processor.extract(f, d)
        assert isinstance(exc_info.value.__cause__, OutsideDestinationError)


@pytest.mark.parametrize("random_file_size", [1 << 30, 2 << 30])
@pytest.mark.limit_memory("2 MB")
def test_tar_archive_extraction_single_file(random_file_size, tmp_path):
    with TemporaryFile(dir=tmp_path) as tar_file:
        with tarfile.open(fileobj=tar_file, mode="w") as archive:
            with random_file(tmp_path, random_file_size) as fd:
                tarinfo = archive.gettarinfo(arcname="random_file", fileobj=fd)
                archive.addfile(tarinfo, fd)

        tar_file.flush()
        tar_file.seek(0)

        processor = archive_extractors.TarExtractor()
        processor.extract(tar_file, tmp_path)

        filepath = tmp_path / "random_file"
        assert filepath.is_file()
        assert filepath.stat().st_size != 0
