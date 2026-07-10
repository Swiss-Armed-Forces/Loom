"""Unit tests for shell infrastructure: ShellIndexCollector, open_shell_db, TestCliShell
(in-process), TestCliTabComplete."""

import argparse
import io
import sqlite3
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import NamedTuple
from uuid import uuid4

import pytest
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService

from worker.create_archive.tasks.archive_cli import (
    CLI_ENTRYPOINT_FILENAME,
    SHELL_INDEX_FILENAME,
    cmd_shell,
)
from worker.create_archive.tasks.archive_cli._db import (
    SHELL_DB_SCHEMA,
    ShellIndexCollector,
    open_shell_db,
)
from worker.create_archive.tasks.archive_cli._shell import ShellCompleter
from worker.create_archive.tasks.archive_cli._types import StorageEntry
from worker.utils.archive import build_archive, simple_entries


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class TestCliShell:
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


class TestShellIndexCollector:
    """Unit tests for ShellIndexCollector — no filesystem needed."""

    def test_registers_vpath_in_files_and_file_id(self, tmp_path: Path) -> None:
        c = ShellIndexCollector(tmp_path / "collector.db")
        file_id = str(uuid4())
        sid = str(uuid4())
        c.add_file(
            "test/docs/report.pdf", file_id, "some.json", [StorageEntry(sid, "file")]
        )
        row = c.connection.execute(
            "SELECT json_filename FROM files WHERE vpath = ?",
            ("test/docs/report.pdf",),
        ).fetchone()
        assert row is not None
        assert row[0] == "some.json"
        row = c.connection.execute(
            "SELECT vpath FROM files WHERE file_id = ?", (file_id,)
        ).fetchone()
        assert row is not None
        assert row[0] == "test/docs/report.pdf"

    def test_registers_storage_id_with_file_role(self, tmp_path: Path) -> None:
        sid = str(uuid4())
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file("test/note.txt", str(uuid4()), "x.json", [StorageEntry(sid, "file")])
        rows = c.connection.execute(
            "SELECT role FROM storage WHERE storage_id = ? AND vpath = ?",
            (sid, "test/note.txt"),
        ).fetchall()
        assert ("file",) in rows

    def test_registers_thumbnail_id(self, tmp_path: Path) -> None:
        tid = str(uuid4())
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file(
            "test/note.txt",
            str(uuid4()),
            "x.json",
            [StorageEntry(str(uuid4()), "file"), StorageEntry(tid, "thumbnail")],
        )
        rows = c.connection.execute(
            "SELECT role FROM storage WHERE storage_id = ? AND vpath = ?",
            (tid, "test/note.txt"),
        ).fetchall()
        assert ("thumbnail",) in rows

    def test_registers_rendered_id(self, tmp_path: Path) -> None:
        rid = str(uuid4())
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file(
            "test/note.txt",
            str(uuid4()),
            "x.json",
            [
                StorageEntry(str(uuid4()), "file"),
                StorageEntry(rid, "rendered:image_data"),
            ],
        )
        rows = c.connection.execute(
            "SELECT role FROM storage WHERE storage_id = ? AND vpath = ?",
            (rid, "test/note.txt"),
        ).fetchall()
        assert ("rendered:image_data",) in rows

    def test_populates_children_at_all_hierarchy_levels(self, tmp_path: Path) -> None:
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file(
            "test/a/b/c.txt",
            str(uuid4()),
            "x.json",
            [StorageEntry(str(uuid4()), "file")],
        )

        def children(parent: str) -> list[str]:
            return [
                row[0]
                for row in c.connection.execute(
                    "SELECT child_name FROM children WHERE parent_path = ?", (parent,)
                ).fetchall()
            ]

        assert "test/" in children("")
        assert "a/" in children("test")
        assert "b/" in children("test/a")
        assert "c.txt" in children("test/a/b")

    def test_deduplicates_children(self, tmp_path: Path) -> None:
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file(
            "test/docs/a.txt",
            str(uuid4()),
            "a.json",
            [StorageEntry(str(uuid4()), "file")],
        )
        c.add_file(
            "test/docs/b.txt",
            str(uuid4()),
            "b.json",
            [StorageEntry(str(uuid4()), "file")],
        )
        rows = c.connection.execute(
            "SELECT child_name FROM children WHERE parent_path = ? AND child_name = ?",
            ("", "test/"),
        ).fetchall()
        assert len(rows) == 1

    def test_ignores_empty_storage_ids(self, tmp_path: Path) -> None:
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file("test/note.txt", str(uuid4()), "x.json", [])
        rows = c.connection.execute(
            "SELECT storage_id FROM storage WHERE vpath = ?", ("test/note.txt",)
        ).fetchall()
        assert len(rows) == 0

    def test_stream_db_roundtrips_via_open_shell_db(self, tmp_path: Path) -> None:
        c = ShellIndexCollector(tmp_path / "collector.db")
        c.add_file(
            "test/docs/report.pdf",
            str(uuid4()),
            "abc.json",
            [StorageEntry(str(uuid4()), "file")],
        )
        (tmp_path / SHELL_INDEX_FILENAME).write_bytes(b"".join(c.stream_db()))
        db = open_shell_db(tmp_path)
        row = db.execute(
            "SELECT json_filename FROM files WHERE vpath = ?",
            ("test/docs/report.pdf",),
        ).fetchone()
        assert row is not None
        assert row[0] == "abc.json"


class TestOpenShellDb:
    """Unit tests for open_shell_db."""

    def _write_db(self, tmp_path: Path) -> None:
        db = sqlite3.connect(str(tmp_path / SHELL_INDEX_FILENAME))
        db.executescript(SHELL_DB_SCHEMA)
        db.execute(
            "INSERT INTO files VALUES (?, ?, ?)", ("docs/a.txt", "abc.json", "fid1")
        )
        db.execute("INSERT INTO children VALUES (?, ?)", ("", "docs/"))
        db.commit()
        db.close()

    def test_opens_valid_db(self, tmp_path: Path) -> None:
        self._write_db(tmp_path)
        db = open_shell_db(tmp_path)
        row = db.execute(
            "SELECT json_filename FROM files WHERE vpath = ?", ("docs/a.txt",)
        ).fetchone()
        assert row is not None
        assert row[0] == "abc.json"

    def test_exits_when_file_absent(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc_info:
            open_shell_db(tmp_path)
        assert exc_info.value.code == 2

    def test_exits_on_corrupt_db(self, tmp_path: Path) -> None:
        (tmp_path / SHELL_INDEX_FILENAME).write_bytes(b"not a sqlite db")
        with pytest.raises(SystemExit) as exc_info:
            open_shell_db(tmp_path)
        assert exc_info.value.code == 2


class _CompleterContext(NamedTuple):
    completer: ShellCompleter
    archive_dir: Path


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
