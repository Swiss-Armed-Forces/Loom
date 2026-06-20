import subprocess
import sys
from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService

from worker.create_archive.tasks.archive_format import (
    CLI_DESCRIPTION,
    CLI_FILENAME,
    ERR_NO_FILE_FOUND,
    SHELL_PROMPT,
)
from worker.utils.archive import build_archive, simple_entries


def _run_shell(archive_dir: Path, commands: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_FILENAME)],
        input=commands,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class TestCliShell:
    def test_no_args_launches_shell(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "exit\n")

        assert result.returncode == 0
        assert SHELL_PROMPT in result.stdout

    def test_shell_subcommand_launches_shell(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = subprocess.run(
            [sys.executable, str(archive_dir / CLI_FILENAME), "shell"],
            input="exit\n",
            capture_output=True,
            text=True,
            check=False,
            cwd=archive_dir,
        )

        assert result.returncode == 0
        assert SHELL_PROMPT in result.stdout

    def test_shell_ls_lists_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "ls\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_shell_grep_finds_file(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "grep report\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_shell_tree_shows_hierarchy(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"pdf", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "tree\nexit\n")

        assert result.returncode == 0
        assert "docs" in result.stdout
        assert "images" in result.stdout

    def test_shell_invalid_command_stays_running(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "invalidcmd\nexit\n")

        assert result.returncode == 0

    def test_shell_error_command_stays_running(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "ls nonexistent\nexit\n")

        assert result.returncode == 0
        assert ERR_NO_FILE_FOUND in result.stderr

    def test_shell_help_prints_help(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "help\nexit\n")

        assert result.returncode == 0
        assert CLI_DESCRIPTION in result.stdout

    def test_shell_eof_exits_cleanly(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "")

        assert result.returncode == 0
