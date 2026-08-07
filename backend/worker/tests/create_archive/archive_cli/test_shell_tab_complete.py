from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_helpers import build_archive, simple_entries

from worker.create_archive.tasks.archive_cli._constants import FILES_INDEX_DIR
from worker.create_archive.tasks.archive_cli._db import open_shell_db
from worker.create_archive.tasks.archive_cli._shell import ShellCompleter


class TestCliTabComplete:
    def _make_completer(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> ShellCompleter:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"file.txt": b"hello world"}),
            file_storage_service_inmemory,
        )
        db = open_shell_db(archive_dir)
        index_dir = archive_dir / FILES_INDEX_DIR
        return ShellCompleter(db=db, index_dir=index_dir)

    def test_info_field_completes_after_path(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
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
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
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
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "info test"
        begidx = len("info ")
        result = completer.get_completions("test", line, begidx)

        assert any("test" in c for c in result)

    def test_find_flag_completes_options(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        result = completer.get_completions("-", "find -", 5)
        assert "-attr" in result
        assert "-name" in result
        assert "-iname" in result

    def test_find_flag_completes_partial(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        result = completer.get_completions("-a", "find -a", 5)
        assert result == ["-attr"]

    def test_grep_flag_completes_options(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        result = completer.get_completions("-", "grep -", 5)
        assert "-i" in result
        assert "--ignore-case" in result
        assert "-l" in result
        assert "-f" in result
        assert "--field" in result

    def test_extract_flag_completes_options(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        for cmd in ("x", "extract"):
            result = completer.get_completions("--no", f"{cmd} --no", len(cmd) + 1)
            assert "--no-recursion" in result
            assert "--no-thumbnails" in result
            assert "--no-rendered" in result
            assert "--no-index" in result
            assert "--no-meta" in result

    def test_info_flag_completes_options(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        result = completer.get_completions("-", "info -", 5)
        assert "-j" in result
        assert "--json" in result

    def test_all_commands_complete_help_flag(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        for cmd in (
            "ls",
            "list",
            "cat",
            "translate",
            "tree",
            "id",
            "cd",
            "pwd",
            "clear",
            "history",
        ):
            result = completer.get_completions("-h", f"{cmd} -h", len(cmd) + 1)
            assert "-h" in result, f"expected -h completion for {cmd!r}"
            result_long = completer.get_completions("--h", f"{cmd} --h", len(cmd) + 1)
            assert "--help" in result_long, f"expected --help completion for {cmd!r}"

    def test_exit_and_quit_return_no_flags(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        for cmd in ("exit", "quit"):
            result = completer.get_completions("-", f"{cmd} -", len(cmd) + 1)
            assert result == [], f"expected no flag completions for {cmd!r}"

    def test_find_attr_completes_field_names(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "find -attr "
        begidx = len(line)
        result = completer.get_completions("", line, begidx)

        assert len(result) > 0
        assert any("content" in c for c in result)

    def test_find_attr_completes_partial_field(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "find -attr con"
        begidx = len("find -attr ")
        result = completer.get_completions("con", line, begidx)

        assert all(c.startswith("con") for c in result)
        assert any("content" in c for c in result)

    def test_find_no_completions_without_attr(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        result = completer.get_completions("", "find ", 5)

        assert result == []

    def test_grep_field_flag_completes_field_names(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "grep pattern -f "
        begidx = len(line)
        result = completer.get_completions("", line, begidx)

        assert len(result) > 0
        assert any("content" in c for c in result)

    def test_grep_long_field_flag_completes_field_names(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        completer = self._make_completer(tmp_path, file_storage_service_inmemory)
        completer.cwd = ""
        line = "grep pattern --field "
        begidx = len(line)
        result = completer.get_completions("", line, begidx)

        assert len(result) > 0
        assert any("content" in c for c in result)
