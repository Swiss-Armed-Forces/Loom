import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from worker.create_archive.tasks.archive_cli import SHELL_INDEX_FILENAME
from worker.create_archive.tasks.archive_cli._db import (
    SHELL_DB_SCHEMA,
    ShellIndexCollector,
    open_shell_db,
)
from worker.create_archive.tasks.archive_cli._types import StorageEntry


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
