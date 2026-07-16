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


class TestCliGrep:
    def test_finds_match_shows_field_and_value(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "important"])

        assert result.returncode == 0
        assert "important_doc.txt [full_name]: important_doc.txt" in result.stdout

    def test_keys_not_searched(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        # "full_name" is a JSON key — it should only match if also present as a value
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        # "full_name" is a key; searching for it should not match (it's not a value)
        result = _run(archive_dir, ["grep", "^full_name$"])

        assert result.returncode != 0

    def test_no_match_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "xyzzy_no_match"])

        assert result.returncode != 0
        assert result.stdout == ""

    def test_case_sensitive_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "IMPORTANT"])

        assert result.returncode != 0

    def test_ignore_case_flag(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "-i", "IMPORTANT"])

        assert result.returncode == 0
        assert "important_doc.txt" in result.stdout

    def test_files_with_matches_flag(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "-l", "report"])

        assert result.returncode == 0
        assert result.stdout.strip() == "test/report.pdf"
        assert "[" not in result.stdout

    def test_regex_pattern(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"pdf", "image.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", r"report\.(pdf|txt)"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "image.jpg" not in result.stdout

    def test_invalid_regex_exits_with_error(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "[unclosed"])

        assert result.returncode == 2
        assert "invalid pattern" in result.stderr

    def test_help_describes_usage(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "--help"])

        assert result.returncode == 0
        assert "field.path" in result.stdout
