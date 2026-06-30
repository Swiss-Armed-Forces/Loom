import shlex
import subprocess
import sys
from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService

from worker.create_archive.tasks.archive_format import (
    CLI_DESCRIPTION,
    CLI_FILENAME,
    ERR_NO_FILE_FOUND,
    FILES_INDEX_DIR,
    SHELL_PROMPT,
    IndexEntry,
    _list_children,
    _resolve_cwd,
    _shell_escape,
    _shell_unescape,
    _ShellCompleter,
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
        result = _run_shell(archive_dir, "cd docs\npwd\nexit\n")

        assert result.returncode == 0
        assert "/docs\n" in result.stdout

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
        result = _run_shell(archive_dir, "cd docs\ncd ..\npwd\nexit\n")

        assert result.returncode == 0
        # pwd prints "/" followed by a newline; this substring is unique to that output
        assert "/\n" in result.stdout

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
        result = _run_shell(archive_dir, "cd docs\ncd /\npwd\nexit\n")

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
        result = _run_shell(archive_dir, "cd docs\nls\nexit\n")

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
        result = _run_shell(archive_dir, "ls\nexit\n")

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
        result = _run_shell(archive_dir, "cd docs\ngrep alpha\nexit\n")

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
        result = _run_shell(archive_dir, "cd docs\nfind\nexit\n")

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
    ) -> _ShellCompleter:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(files),
            file_storage_service_inmemory,
        )
        return _ShellCompleter(index_dir=archive_dir / FILES_INDEX_DIR)

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
        c.cwd = "docs"
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
        c.cwd = "docs"
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
        result = _run_shell(archive_dir, 'cd "my reports"\nls\nexit\n')

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
        result = _run_shell(archive_dir, "cd my\\ reports\nls\nexit\n")

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


class TestResolveCwd:
    """Unit tests for _resolve_cwd — a pure function, no filesystem needed."""

    def test_root_is_empty_string(self) -> None:
        assert _resolve_cwd("", "") == ""

    def test_descend_one_level(self) -> None:
        assert _resolve_cwd("", "docs") == "docs"

    def test_descend_two_levels(self) -> None:
        assert _resolve_cwd("docs", "reports") == "docs/reports"

    def test_dotdot_goes_up(self) -> None:
        assert _resolve_cwd("docs", "..") == ""

    def test_dotdot_from_root_stays_at_root(self) -> None:
        assert _resolve_cwd("", "..") == ""

    def test_dotdot_beyond_root_clamps(self) -> None:
        assert _resolve_cwd("docs", "../..") == ""

    def test_dot_stays(self) -> None:
        assert _resolve_cwd("docs", ".") == "docs"

    def test_absolute_target(self) -> None:
        assert _resolve_cwd("docs", "/images") == "images"

    def test_cd_root_slash(self) -> None:
        assert _resolve_cwd("docs/reports", "/") == ""

    def test_mixed_dotdot_and_segment(self) -> None:
        assert _resolve_cwd("a/b/c", "../../x") == "a/x"


class TestListChildren:
    """Unit tests for _list_children — no filesystem needed."""

    def _entry(self, name: str) -> IndexEntry:
        return IndexEntry(name=name, storage_id="x", meta={})

    def test_files_at_root(self) -> None:
        entries = [self._entry("a.pdf"), self._entry("b.txt")]
        assert sorted(_list_children("", entries)) == ["a.pdf", "b.txt"]

    def test_virtual_dirs_at_root(self) -> None:
        entries = [self._entry("docs/a.pdf"), self._entry("images/b.jpg")]
        children = _list_children("", entries)
        assert "docs/" in children
        assert "images/" in children

    def test_files_under_cwd(self) -> None:
        entries = [self._entry("docs/a.pdf"), self._entry("docs/b.pdf")]
        children = _list_children("docs", entries)
        assert "a.pdf" in children
        assert "b.pdf" in children

    def test_no_blank_entry_for_exact_prefix_match(self) -> None:
        """An entry whose vpath equals the prefix exactly must not produce a blank
        line."""
        entries = [self._entry("docs/")]
        children = _list_children("docs", entries)
        assert "" not in children

    def test_double_slash_prefix_normalised(self) -> None:
        entries = [self._entry("//host/dir/file.pdf")]
        children = _list_children("", entries)
        assert "host/" in children
        assert "" not in children


class TestEscapeHelpers:
    """Unit tests for _shell_escape / _shell_unescape."""

    def test_escape_space(self) -> None:
        assert _shell_escape("my file.pdf") == "my\\ file.pdf"

    def test_escape_parens(self) -> None:
        assert _shell_escape("report (draft).pdf") == "report\\ \\(draft\\).pdf"

    def test_escape_at(self) -> None:
        assert _shell_escape("user@host") == "user\\@host"

    def test_unescape_space(self) -> None:
        assert _shell_unescape("my\\ file.pdf") == "my file.pdf"

    def test_roundtrip_all_special_chars(self) -> None:
        for char in " \t\"'`$!#@&;|<>*()?[]{}~":
            name = f"file{char}name.pdf"
            escaped = _shell_escape(name)
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
        result = _run_shell(archive_dir, "cd docs\ncd nonexistent\npwd\nexit\n")

        assert result.returncode == 0
        assert "nonexistent" in result.stderr
        assert "/docs\n" in result.stdout

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
        result = _run_shell(archive_dir, "clear\nls\nexit\n")

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
        result = _run_shell(archive_dir, "cd docs\ntree\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "images" not in result.stdout


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
            [sys.executable, str(archive_dir / CLI_FILENAME), "ls"],
            capture_output=True,
            text=True,
            check=False,
            cwd=archive_dir,
        )

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout
        assert "images/photo.jpg" in result.stdout
