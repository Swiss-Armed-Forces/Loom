import argparse
import io
import shlex
import sqlite3
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import NamedTuple

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_helpers import build_archive, simple_entries

from worker.create_archive.tasks.archive_cli import (
    CLI_DESCRIPTION,
    CLI_ENTRYPOINT_FILENAME,
    ERR_NO_FILE_FOUND,
    FILES_INDEX_DIR,
    SHELL_INDEX_FILENAME,
    SHELL_PROMPT,
    cmd_shell,
)
from worker.create_archive.tasks.archive_cli._db import (
    SHELL_DB_SCHEMA,
    open_shell_db,
)
from worker.create_archive.tasks.archive_cli._shell import (
    ShellCompleter,
    shell_escape,
    shell_unescape,
)


def _run_shell(archive_dir: Path, commands: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)],
        input=commands,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class _CompleterContext(NamedTuple):
    completer: ShellCompleter
    archive_dir: Path


class TestCliShellInProcess:
    def test_ctrl_c_does_not_exit_shell(self, tmp_path: Path) -> None:
        call_count = 0

        def mock_input(_prompt: str = "") -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise KeyboardInterrupt
            return "exit"

        db = sqlite3.connect(str(tmp_path / SHELL_INDEX_FILENAME))
        db.executescript(SHELL_DB_SCHEMA)
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_shell(
                argparse.Namespace(),
                db=db,
                history_file=None,
                input_fn=mock_input,
            )

        assert "^C" in out.getvalue()


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
            [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME), "shell"],
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
        # simple_entries uses source="test", so vpaths are under test/
        result = _run_shell(archive_dir, "cd test\nls\nexit\n")

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

    def test_exit_command_exits_shell(
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

    def test_shell_saves_history_file(
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
        history_file = archive_dir / ".loom_history"
        assert history_file.exists()
        assert "ls" in history_file.read_text()

    def test_shell_loads_existing_history_file(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        history_file = archive_dir / ".loom_history"
        history_file.write_text("ls\ngrep report\n")

        result = _run_shell(archive_dir, "exit\n")

        assert result.returncode == 0


class TestCliShellNavigation:
    def test_pwd_at_root(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "pwd\nexit\n")

        assert result.returncode == 0
        assert "/\n" in result.stdout

    def test_cd_changes_directory(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        # simple_entries uses source="test", so navigate through test/ first
        result = _run_shell(archive_dir, "cd test/docs\npwd\nexit\n")

        assert result.returncode == 0
        assert "/test/docs\n" in result.stdout

    def test_cd_dotdot(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\ncd ..\npwd\nexit\n")

        assert result.returncode == 0
        assert "/test\n" in result.stdout

    def test_cd_invalid_directory(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd nonexistent\nexit\n")

        assert result.returncode == 0
        assert "nonexistent" in result.stderr

    def test_cd_root(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\ncd /\npwd\nexit\n")

        assert result.returncode == 0
        assert "/\n" in result.stdout

    def test_ls_scoped_to_cwd(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.pdf": b"data", "images/b.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\nls\nexit\n")

        assert result.returncode == 0
        assert "a.pdf" in result.stdout
        assert "b.jpg" not in result.stdout

    def test_ls_shows_virtual_dirs(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.pdf": b"data", "images/b.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        # Navigate into the source directory first; virtual dirs show there
        result = _run_shell(archive_dir, "cd test\nls\nexit\n")

        assert result.returncode == 0
        assert "docs/" in result.stdout

    def test_grep_scoped_to_cwd(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/alpha.pdf": b"data", "images/beta.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\ngrep alpha\nexit\n")

        assert result.returncode == 0
        assert "docs/alpha.pdf" in result.stdout
        assert "beta" not in result.stdout

    def test_find_lists_all_under_cwd(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.pdf": b"data", "images/b.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\nfind\nexit\n")

        assert result.returncode == 0
        assert "a.pdf" in result.stdout
        assert "b.jpg" not in result.stdout

    def test_find_name(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "docs/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "find -name *.pdf\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "photo.jpg" not in result.stdout

    def test_find_iname(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/Report.PDF": b"data", "docs/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "find -iname *.pdf\nexit\n")

        assert result.returncode == 0
        assert "Report.PDF" in result.stdout
        assert "photo.jpg" not in result.stdout

    def test_cd_with_double_slash_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        """Entries with //host/dir/ prefixes are navigable via their bare component."""
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "//loom-prod.intake/reports/q1.pdf": b"data",
                    "//loom-prod.intake/images/photo.jpg": b"img",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd loom-prod.intake\ncd reports\nls\nexit\n")

        assert result.returncode == 0
        assert "q1.pdf" in result.stdout
        assert "photo.jpg" not in result.stdout


class TestShellCompleter:
    def _make_completer(
        self,
        files: dict[str, bytes],
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> ShellCompleter:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(files),
            file_storage_service_inmemory,
        )
        db = open_shell_db(archive_dir)
        return ShellCompleter(db=db, index_dir=archive_dir / FILES_INDEX_DIR)

    def test_completes_command_names(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"report.pdf": b"data"}, tmp_path, file_storage_service_inmemory
        )
        matches = c.get_completions("ls", "", 0)
        assert "ls" in matches
        assert all(m.startswith("ls") for m in matches)

    def test_completes_partial_command(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"report.pdf": b"data"}, tmp_path, file_storage_service_inmemory
        )
        matches = c.get_completions("ex", "", 0)
        assert "exit" in matches
        assert "extract" in matches
        assert "ls" not in matches

    def test_cd_completes_virtual_dirs(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"docs/report.pdf": b"data", "images/photo.jpg": b"img"},
            tmp_path,
            file_storage_service_inmemory,
        )
        # simple_entries uses source="test", so dirs appear under test/
        c.cwd = "test"
        matches = c.get_completions("", "cd ", 3)
        assert "docs/" in matches
        assert "images/" in matches

    def test_cd_does_not_complete_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"report.pdf": b"data"}, tmp_path, file_storage_service_inmemory
        )
        matches = c.get_completions("", "cd ", 3)
        assert "report.pdf" not in matches

    def test_cd_completes_partial_dir(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"docs/report.pdf": b"data", "images/photo.jpg": b"img"},
            tmp_path,
            file_storage_service_inmemory,
        )
        # Navigate into test/ first since simple_entries uses source="test"
        c.cwd = "test"
        matches = c.get_completions("do", "cd do", 3)
        assert "docs/" in matches
        assert "images/" not in matches

    def test_cd_updates_after_directory_change(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"docs/reports/q1.pdf": b"data", "docs/images/photo.jpg": b"img"},
            tmp_path,
            file_storage_service_inmemory,
        )
        c.cwd = "test/docs"
        matches = c.get_completions("", "cd ", 3)
        assert "reports/" in matches
        assert "images/" in matches

    def test_ls_completes_files_and_dirs(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"docs/report.pdf": b"data", "notes.txt": b"text"},
            tmp_path,
            file_storage_service_inmemory,
        )
        # Navigate into test/ to see the actual files and dirs
        c.cwd = "test"
        matches = c.get_completions("", "ls ", 3)
        assert "docs/" in matches
        assert "notes.txt" in matches

    def test_no_completions_for_grep(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"report.pdf": b"data"}, tmp_path, file_storage_service_inmemory
        )
        matches = c.get_completions("", "grep ", 5)
        assert matches == []

    def test_completer_escapes_spaces_in_dirname(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"my reports/q1.pdf": b"data"},
            tmp_path,
            file_storage_service_inmemory,
        )
        # Navigate into test/ where the space-containing dir lives
        c.cwd = "test"
        matches = c.get_completions("", "cd ", 3)
        assert "my\\ reports/" in matches

    def test_completer_escapes_special_chars(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        c = self._make_completer(
            {"docs/report (draft).pdf": b"data"},
            tmp_path,
            file_storage_service_inmemory,
        )
        c.cwd = "test/docs"
        matches = c.get_completions("", "ls ", 3)
        assert "report\\ \\(draft\\).pdf" in matches

    def test_completer_handles_space_in_path_via_full_arg(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        """When readline splits on space, _full_path_arg reassembles the path."""
        c = self._make_completer(
            {"my reports/q1.pdf": b"data", "my reports/q2.pdf": b"v2"},
            tmp_path,
            file_storage_service_inmemory,
        )
        # Set cwd to "test" so that "my reports/" resolves to "test/my reports/"
        c.cwd = "test"
        # Simulate: user typed "ls my\ reports/" and readline split at space,
        # giving text="reports/", line="ls my\ reports/", begidx=7
        matches = c.get_completions("reports/", "ls my\\ reports/", 7)
        # Should complete to "reports/q1.pdf" and "reports/q2.pdf"
        assert any("q1.pdf" in m for m in matches)
        assert any("q2.pdf" in m for m in matches)


class TestShellWithSpecialFilenames:
    def test_shell_ls_quoted_path_with_space(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"my reports/q1.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        # Navigate through test/ first since simple_entries uses source="test"
        result = _run_shell(archive_dir, 'cd test\ncd "my reports"\nls\nexit\n')

        assert result.returncode == 0
        assert "q1.pdf" in result.stdout

    def test_shell_ls_backslash_escaped_path(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"my reports/q1.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test\ncd my\\ reports\nls\nexit\n")

        assert result.returncode == 0
        assert "q1.pdf" in result.stdout

    def test_shell_find_filename_with_special_chars(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {"docs/report (draft).pdf": b"data", "docs/other.pdf": b"v2"}
            ),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, 'find -name "*.pdf"\nexit\n')

        assert result.returncode == 0
        assert "report (draft).pdf" in result.stdout
        assert "other.pdf" in result.stdout


class TestEscapeHelpers:
    """Unit tests for shell_escape / shell_unescape."""

    def test_escape_space(self) -> None:
        assert shell_escape("my file.pdf") == "my\\ file.pdf"

    def test_escape_parens(self) -> None:
        assert shell_escape("report (draft).pdf") == "report\\ \\(draft\\).pdf"

    def test_escape_at(self) -> None:
        assert shell_escape("user@host") == "user\\@host"

    def test_unescape_space(self) -> None:
        assert shell_unescape("my\\ file.pdf") == "my file.pdf"

    def test_roundtrip_all_special_chars(self) -> None:
        for char in " \t\"'`$!#@&;|<>*()?[]{}~":
            name = f"file{char}name.pdf"
            escaped = shell_escape(name)
            assert (
                shlex.split(f"ls {escaped}")[1] == name
            ), f"round-trip failed for char {char!r}"


class TestCliShellNavigationExtra:
    """Additional navigation tests that extend TestCliShellNavigation."""

    def test_cd_dotdot_from_root_stays_at_root(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd ..\npwd\nexit\n")

        assert result.returncode == 0
        assert "/\n" in result.stdout

    def test_cd_invalid_does_not_change_cwd(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\ncd nonexistent\npwd\nexit\n")

        assert result.returncode == 0
        assert "nonexistent" in result.stderr
        assert "/test/docs\n" in result.stdout

    def test_clear_does_not_crash_shell(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "clear\ncd test\nls\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_tree_scoped_excludes_other_dirs(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "cd test/docs\ntree\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "images" not in result.stdout


class TestCliTabComplete:
    def _make_completer(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> _CompleterContext:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"file.txt": b"hello world"}),
            file_storage_service_inmemory,
        )
        db = open_shell_db(archive_dir)
        index_dir = archive_dir / "files_index"
        completer = ShellCompleter(db=db, index_dir=index_dir)
        return _CompleterContext(completer=completer, archive_dir=archive_dir)

    def test_info_field_completes_after_path(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer, _ = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "info test/file.txt con"
        begidx = len("info test/file.txt ")
        result = completer.get_completions("con", line, begidx)

        assert any(c.startswith("con") for c in result)

    def test_info_field_completes_empty_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer, _ = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "info test/file.txt "
        begidx = len(line)
        result = completer.get_completions("", line, begidx)

        assert len(result) > 0
        assert any("storage_data" in c for c in result)

    def test_info_path_still_completes_first_arg(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer, _ = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "info test"
        begidx = len("info ")
        result = completer.get_completions("test", line, begidx)

        assert any("test" in c for c in result)
