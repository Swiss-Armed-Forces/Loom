import subprocess
import sys
from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_helpers import build_archive, simple_entries

from worker.create_archive.tasks.archive_cli import CLI_ENTRYPOINT_FILENAME


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class TestCliLs:
    def test_lists_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"pdf"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls"])

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout

    def test_empty_archive(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path, simple_entries({}), file_storage_service_inmemory
        )
        result = _run(archive_dir, ["ls"])

        assert result.returncode != 0
        assert "no file found matching" in result.stderr

    def test_glob_filters_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "docs/report.pdf": b"pdf",
                    "docs/notes.txt": b"txt",
                    "images/photo.jpg": b"img",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "test/docs/*.txt"])

        assert result.returncode == 0
        assert "docs/notes.txt" in result.stdout
        assert "docs/report.pdf" not in result.stdout
        assert "images/photo.jpg" not in result.stdout

    def test_glob_matches_across_directories(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "a/foo.txt": b"a",
                    "b/bar.txt": b"b",
                    "c/img.png": b"c",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "*.txt"])

        assert result.returncode == 0
        assert "a/foo.txt" in result.stdout
        assert "b/bar.txt" in result.stdout
        assert "c/img.png" not in result.stdout

    def test_directory_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "docs/report.pdf": b"pdf",
                    "images/photo.jpg": b"img",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "test/docs/"])

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout
        assert "images/photo.jpg" not in result.stdout


class TestCliStandalone:
    """Tests for non-shell (standalone) CLI invocations."""

    def test_ls_no_args_lists_all(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = subprocess.run(
            [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME), "ls"],
            capture_output=True,
            text=True,
            check=False,
            cwd=archive_dir,
        )

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout
        assert "images/photo.jpg" in result.stdout
