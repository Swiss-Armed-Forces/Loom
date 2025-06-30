import tempfile
from pathlib import Path

from pydantic import BaseModel

from worker.index_file.processor.extractor.archive_extractors import BinwalkExtractor

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
    # Get all files and directories recursively
    all_items: list[Path] = list(base_path.rglob("*"))
    all_files: list[Path] = [p for p in all_items if p.is_file()]
    all_dirs: list[Path] = [p for p in all_items if p.is_dir()]

    # Assert the exact structure using relative paths
    relative_files: list[Path] = [p.relative_to(base_path) for p in all_files]
    relative_dirs: list[Path] = [p.relative_to(base_path) for p in all_dirs]

    assert set(relative_files) == set(
        expected.files
    ), f"Files mismatch. Expected: {expected.files}, Got: {relative_files}"
    assert set(relative_dirs) == set(
        expected.dirs
    ), f"Directories mismatch. Expected: {expected.dirs}, Got: {relative_dirs}"


def test_binwalk_extraction_files():
    test_asset = TEST_ASSETS_DIR / "single_file.tar.gz"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)

        base_path = Path(d)

        expected_structure = ExpectedDirectoryStructure(
            files=[Path("0x0/0"), Path("0x0/0.gz")],
            dirs=[Path("0x0")],
        )

        assert_directory_structure(base_path, expected_structure)


def test_binwalk_extraction_files_directory_not_exist():
    test_asset = TEST_ASSETS_DIR / "actually_text.wav"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)

        base_path = Path(d)

        expected_structure = ExpectedDirectoryStructure()

        assert_directory_structure(base_path, expected_structure)


def test_binwalk_extraction_files_iso():
    test_asset = TEST_ASSETS_DIR / "testiso.iso"

    processor = BinwalkExtractor()

    with test_asset.open("rb") as f, tempfile.TemporaryDirectory() as d:
        processor.extract(f, d)

        base_path = Path(d)

        expected_structure = ExpectedDirectoryStructure(
            files=[Path("0x0/0.iso"), Path("0x0/iso-root/TESTFILE.TXT")],
            dirs=[Path("0x0"), Path("0x0/iso-root")],
        )

        assert_directory_structure(base_path, expected_structure)
