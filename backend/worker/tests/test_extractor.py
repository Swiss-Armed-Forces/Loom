import os
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryFile
from typing import IO, Callable, ContextManager, Iterator
from zipfile import ZipFile

import pytest
from common.services.lazybytes_service import LazyBytesService
from common.utils.random_file import random_file
from pydantic import BaseModel
from zstandard import ZstdCompressionParameters, ZstdCompressor

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    ExtractorBase,
    NamedFileExtractorBase,
)
from worker.index_file.extractor.binwalk_extractor import BinwalkExtractor
from worker.index_file.extractor.pcap_extractor import PcapExtractor
from worker.index_file.extractor.pst_extractor import (
    PstExtractor,
)
from worker.index_file.extractor.tar_extractor import TarExtractor
from worker.index_file.extractor.zip_extractor import ZipExtractor
from worker.index_file.extractor.zstd_extractor import (
    ZSTD_EXTRACTOR_READ_CHUNK_SIZE__BYTES,
    ZstdExtractor,
)

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


class ExpectedDirectoryStructure(BaseModel):
    """Pydantic model for expected directory structure."""

    files: list[Path] = []
    dirs: list[Path] = []


def assert_directory_structure(
    base_path: Path, expected: ExpectedDirectoryStructure
) -> None:
    """Assert that a directory matches the expected structure.

    Args:
        base_path: Path to the directory to check
        expected: ExpectedDirectoryStructure containing expected files and directories

    Raises:
        AssertionError: If the directory structure doesn't match expectations
    """
    all_items: list[Path] = list(base_path.rglob("*"))
    all_files: list[Path] = [p for p in all_items if p.is_file()]
    all_dirs: list[Path] = [p for p in all_items if p.is_dir()]

    relative_files: list[Path] = [p.relative_to(base_path) for p in all_files]
    relative_dirs: list[Path] = [p.relative_to(base_path) for p in all_dirs]

    assert set(relative_files) == set(
        expected.files
    ), f"Files mismatch. Expected: {expected.files}, Got: {relative_files}"
    assert set(relative_dirs) == set(
        expected.dirs
    ), f"Directories mismatch. Expected: {expected.dirs}, Got: {relative_dirs}"


def count_files(directory: str) -> int:
    """Count total number of files in a directory recursively."""
    return sum(len(filenames) for _, _, filenames in os.walk(directory))


@pytest.mark.parametrize(
    "extractor_class,unsupported_file,file_type",
    [
        (PstExtractor, "evil.zip", "application/zip"),
        (PcapExtractor, "evil.zip", "application/zip"),
        (BinwalkExtractor, "actually_text.wav", "audio/x-wav"),
        (TarExtractor, "pdf-annotated.pdf", "application/pdf"),
        (TarExtractor, "testarchive.zip", "application/zip"),
        (TarExtractor, "testiso.iso", "application/x-iso9660-image"),
        (ZipExtractor, "empty_file.tar.gz", "application/x-tar"),
    ],
)
def test_extractor_unsupported(
    extractor_class: type[ExtractorBase],
    unsupported_file: str,
    file_type: str,
    lazybytes_service_inmemory: LazyBytesService,
):
    """Test that extractors raise ExtractNotSupported for unsupported files."""
    processor = extractor_class()
    filepath = TEST_ASSETS_DIR / unsupported_file

    with (
        filepath.open("rb") as f,
        tempfile.TemporaryDirectory() as d,
        tempfile.NamedTemporaryFile() as out_content,
    ):
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        with pytest.raises(ExtractNotSupported):
            processor.extract(lazy_bytes, file_type, d, out_content)


# pylint: disable=too-many-arguments,too-many-positional-arguments
@pytest.mark.parametrize(
    "extractor_class,test_file,file_type,file_count,has_stdout,expected_structure",
    [
        (
            PstExtractor,
            "testarchive.pst",
            "application/vnd.ms-outlook",
            1,
            False,
            None,
        ),
        (
            PcapExtractor,
            "http.pcap",
            "application/vnd.tcpdump.pcap",
            None,
            True,
            None,
        ),
        (
            BinwalkExtractor,
            "single_file.tar.gz",
            "application/gzip",
            None,
            False,
            ExpectedDirectoryStructure(
                files=[Path("0x0/0"), Path("0x0/0.gz")],
                dirs=[Path("0x0")],
            ),
        ),
        (
            BinwalkExtractor,
            "testiso.iso",
            "application/x-iso9660-image",
            None,
            False,
            ExpectedDirectoryStructure(
                files=[Path("0x0/0.iso"), Path("0x0/iso-root/TESTFILE.TXT")],
                dirs=[Path("0x0"), Path("0x0/iso-root")],
            ),
        ),
        (TarExtractor, "empty_file.tar", "application/x-tar", 1, False, None),
        (TarExtractor, "empty_file.tar.gz", "application/x-tar", 1, False, None),
        (TarExtractor, "hidden_file.tar", "application/x-tar", 1, False, None),
        (TarExtractor, "hidden_file.tar.gz", "application/x-tar", 1, False, None),
        (TarExtractor, "multi_file.tar", "application/x-tar", 3, False, None),
        (TarExtractor, "multi_file.tar.gz", "application/x-tar", 3, False, None),
        (TarExtractor, "sub_folder.tar", "application/x-tar", 2, False, None),
        (TarExtractor, "sub_folder.tar.gz", "application/x-tar", 2, False, None),
        (
            TarExtractor,
            "sub_sub_folder.tar",
            "application/x-tar",
            3,
            False,
            ExpectedDirectoryStructure(
                files=[
                    Path(
                        "sub_sub_folder_top_tar/sub_sub_folder_bot_tar/child_file_tar"
                    ),
                    Path("sub_sub_folder_top_tar/middle_file_tar"),
                    Path("super_parent_file_tar"),
                ],
                dirs=[
                    Path("sub_sub_folder_top_tar"),
                    Path("sub_sub_folder_top_tar/sub_sub_folder_bot_tar"),
                ],
            ),
        ),
        (TarExtractor, "sub_sub_folder.tar.gz", "application/x-tar", 3, False, None),
        (ZipExtractor, "archive.zip", "application/zip", 1, False, None),
        (ZipExtractor, "testarchive.zip", "application/zip", 3, False, None),
        (
            ZipExtractor,
            "testarchive_larger.zip",
            "application/zip",
            6,
            False,
            ExpectedDirectoryStructure(
                files=[
                    Path("morestuff/onemore/pdf-annotated.tex"),
                    Path("morestuff/onemore/python.png"),
                    Path("morestuff/home.pdf"),
                    Path("testarchive/emptyfile.ignore"),
                    Path("testarchive/testfile01.txt"),
                    Path("testarchive/testfile02.txt"),
                ],
                dirs=[
                    Path("morestuff"),
                    Path("morestuff/onemore"),
                    Path("testarchive"),
                ],
            ),
        ),
        (
            ZstdExtractor,
            "empty_file.tar.zst",
            "application/zstd",
            1,
            False,
            ExpectedDirectoryStructure(
                files=[Path("0")],
                dirs=[],
            ),
        ),
    ],
)
def test_extractor_extraction(
    extractor_class: type[ExtractorBase],
    test_file: str,
    file_type: str,
    file_count: int | None,
    has_stdout: bool,
    expected_structure: ExpectedDirectoryStructure | None,
    lazybytes_service_inmemory: LazyBytesService,
):
    """Test that extractors correctly extract supported files."""
    processor = extractor_class()
    filepath = TEST_ASSETS_DIR / test_file

    with (
        filepath.open("rb") as f,
        tempfile.TemporaryDirectory() as d,
        tempfile.NamedTemporaryFile() as out_content,
    ):
        lazy_bytes = lazybytes_service_inmemory.from_file(f)
        processor.extract(lazy_bytes, file_type, d, out_content)

        if file_count is not None:
            assert count_files(d) == file_count

        if has_stdout:
            out_content.seek(0)
            assert len(out_content.read()) > 0

        if expected_structure is not None:
            assert_directory_structure(Path(d), expected_structure)


# Type alias for archive factory functions
ArchiveFactory = Callable[[Path, int], ContextManager[IO]]


@contextmanager
def create_tar_test_archive(tmp_path: Path, random_file_size: int) -> Iterator[IO]:
    """Create a tar archive with a large random file for memory testing."""
    with TemporaryFile(dir=tmp_path) as tar_file:
        with tarfile.open(fileobj=tar_file, mode="w") as archive:
            with random_file(tmp_path, random_file_size) as fd:
                tarinfo = archive.gettarinfo(arcname="random_file", fileobj=fd)
                archive.addfile(tarinfo, fd)
        tar_file.flush()
        tar_file.seek(0)
        yield tar_file


@contextmanager
def create_zip_test_archive(tmp_path: Path, random_file_size: int) -> Iterator[IO]:
    """Create a zip archive with a large random file for memory testing."""
    with TemporaryFile(dir=tmp_path) as zip_file:
        with ZipFile(zip_file, "w") as archive:
            with random_file(tmp_path, random_file_size) as fd:
                archive.write(fd.name, "random_file")
        zip_file.flush()
        zip_file.seek(0)
        yield zip_file


@contextmanager
def create_zstd_test_archive(tmp_path: Path, random_file_size: int) -> Iterator[IO]:
    """Create a zstd-compressed file with large random data for memory testing."""
    with NamedTemporaryFile(dir=tmp_path) as zstd_file:
        # window_log controls window size: 2^window_log bytes
        # window_log=15 = 32 KiB, window_log=17 = 128 KiB, window_log=20 = 1 MiB
        cctx = ZstdCompressor(
            compression_params=ZstdCompressionParameters(window_log=15)
        )
        with random_file(tmp_path, random_file_size) as fd:
            with cctx.stream_writer(zstd_file, closefd=False) as compressor:
                while chunk := fd.read(ZSTD_EXTRACTOR_READ_CHUNK_SIZE__BYTES):
                    compressor.write(chunk)
        zstd_file.flush()
        zstd_file.seek(0)
        yield zstd_file


@pytest.mark.parametrize(
    "extractor_class,archive_factory,file_type,expected_output_file",
    [
        (TarExtractor, create_tar_test_archive, "application/x-tar", "random_file"),
        (ZipExtractor, create_zip_test_archive, "application/zip", "random_file"),
        (ZstdExtractor, create_zstd_test_archive, "application/zstd", "0"),
    ],
)
@pytest.mark.parametrize("random_file_size", [1 << 30, 2 << 30])
@pytest.mark.limit_memory("2 MB")
def test_extractor_memory_usage(
    extractor_class: type[NamedFileExtractorBase],
    archive_factory: ArchiveFactory,
    file_type: str,
    expected_output_file: str,
    random_file_size: int,
    tmp_path: Path,
):
    """Test that extractors don't consume excessive memory when processing large
    files."""
    with archive_factory(tmp_path, random_file_size) as archive_file:
        with NamedTemporaryFile() as out_content:
            processor = extractor_class()
            processor.extract_file(archive_file, file_type, str(tmp_path), out_content)

        filepath = tmp_path / expected_output_file
        assert filepath.is_file()
        assert filepath.stat().st_size != 0
