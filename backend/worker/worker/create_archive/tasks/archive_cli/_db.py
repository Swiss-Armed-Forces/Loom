import json
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

from ._constants import ARCHIVE_ROOT, SHELL_INDEX_FILENAME
from ._resolve import resolve_name
from ._types import IndexEntry, ServiceIdResult, StorageEntry


class _FileEntry(NamedTuple):
    vpath: str
    json_filename: str


_DB_STREAM_CHUNK_SIZE = 65536

SHELL_DB_SCHEMA = """\
CREATE TABLE files (
    vpath         TEXT PRIMARY KEY,
    json_filename TEXT NOT NULL,
    file_id       TEXT NOT NULL UNIQUE
);
CREATE TABLE children (
    parent_path TEXT NOT NULL,
    child_name  TEXT NOT NULL,
    PRIMARY KEY (parent_path, child_name)
);
CREATE TABLE storage (
    storage_id TEXT NOT NULL,
    vpath      TEXT NOT NULL,
    role       TEXT NOT NULL,
    PRIMARY KEY (storage_id, vpath, role)
);
"""


def open_shell_db(archive_root: Path = ARCHIVE_ROOT) -> sqlite3.Connection:
    db_path = archive_root / SHELL_INDEX_FILENAME
    if not db_path.exists():
        print(
            f"Error: {SHELL_INDEX_FILENAME} not found. "
            "This archive was created by an older version of Loom and is not supported.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        db = sqlite3.connect(str(db_path))
        db.execute("PRAGMA query_only=1")
        db.execute("PRAGMA temp_store=MEMORY")
        db.execute("PRAGMA cache_size=-2000")
        db.execute("SELECT COUNT(*) FROM files").fetchone()
        return db
    except sqlite3.DatabaseError as exc:
        print(f"Error: {SHELL_INDEX_FILENAME} is corrupt: {exc}", file=sys.stderr)
        sys.exit(2)


def _entries_under_db(db: sqlite3.Connection, prefix: str) -> Iterator[_FileEntry]:
    """Yield (vpath, json_filename) for all files under the given path prefix."""
    if prefix == "":
        cursor = db.execute("SELECT vpath, json_filename FROM files ORDER BY vpath")
    else:
        last_char = prefix[-1]
        if ord(last_char) == 0x10FFFF:
            cursor = db.execute(
                "SELECT vpath, json_filename FROM files"
                " WHERE vpath >= ? ORDER BY vpath",
                (prefix,),
            )
        else:
            upper = prefix[:-1] + chr(ord(last_char) + 1)
            cursor = db.execute(
                "SELECT vpath, json_filename FROM files"
                " WHERE vpath >= ? AND vpath < ? ORDER BY vpath",
                (prefix, upper),
            )
    for row in cursor:
        yield _FileEntry(vpath=row[0], json_filename=row[1])


def _print_tree_from_db(root: str, db: sqlite3.Connection, prefix: str = "") -> None:
    """Print a directory tree using the children table (iterative DFS)."""
    rows = db.execute(
        "SELECT child_name FROM children WHERE parent_path = ? ORDER BY child_name",
        (root,),
    ).fetchall()
    items = [row[0] for row in rows]
    # Stack items: (child_name, parent_path, display_prefix, is_last)
    # Reversed so that the first child is on top of the stack.
    stack: list[tuple[str, str, str, bool]] = list(
        reversed(
            [
                (child, root, prefix, i == len(items) - 1)
                for i, child in enumerate(items)
            ]
        )
    )
    while stack:
        child, parent_root, current_prefix, is_last = stack.pop()
        connector = "└── " if is_last else "├── "
        print(current_prefix + connector + child.rstrip("/"))
        if child.endswith("/"):
            ext = "    " if is_last else "│   "
            child_dir = (
                (parent_root + "/" + child.rstrip("/"))
                if parent_root
                else child.rstrip("/")
            )
            sub_rows = db.execute(
                "SELECT child_name FROM children WHERE parent_path = ? ORDER BY child_name",
                (child_dir,),
            ).fetchall()
            sub_items = [row[0] for row in sub_rows]
            stack.extend(
                reversed(
                    [
                        (
                            sub_child,
                            child_dir,
                            current_prefix + ext,
                            j == len(sub_items) - 1,
                        )
                        for j, sub_child in enumerate(sub_items)
                    ]
                )
            )


def get_json_filename(db: sqlite3.Connection, vpath: str) -> str | None:
    """Return json_filename for the given vpath, or None if not found."""
    row = db.execute(
        "SELECT json_filename FROM files WHERE vpath = ?", (vpath,)
    ).fetchone()
    return row[0] if row is not None else None


def get_children(db: sqlite3.Connection, parent_path: str) -> list[str]:
    """Return child names directly under parent_path, ordered alphabetically."""
    rows = db.execute(
        "SELECT child_name FROM children WHERE parent_path = ? ORDER BY child_name",
        (parent_path,),
    ).fetchall()
    return [row[0] for row in rows]


def directory_exists(db: sqlite3.Connection, dir_path: str) -> bool:
    """Return True if dir_path is a known directory (has children or contains files)."""
    row = db.execute(
        "SELECT 1 FROM children WHERE parent_path = ? LIMIT 1", (dir_path,)
    ).fetchone()
    if row is not None:
        return True
    dir_prefix = dir_path + "/"
    dir_upper = dir_path + chr(ord("/") + 1)
    row = db.execute(
        "SELECT 1 FROM files WHERE vpath >= ? AND vpath < ? LIMIT 1",
        (dir_prefix, dir_upper),
    ).fetchone()
    return row is not None


def get_child_vpaths_under(db: sqlite3.Connection, vpath: str) -> Iterator[str]:
    """Yield vpaths of all files under vpath (non-recursive prefix scan)."""
    cursor = db.execute(
        "SELECT vpath FROM files WHERE vpath >= ? AND vpath < ? ORDER BY vpath",
        (vpath + "/", vpath + chr(ord("/") + 1)),
    )
    for (child_vpath,) in cursor:
        yield child_vpath


def get_storage_results(
    db: sqlite3.Connection, storage_id: str
) -> list[ServiceIdResult]:
    """Return all (vpath, role) pairs for the given storage_id."""
    rows = db.execute(
        "SELECT vpath, role FROM storage WHERE storage_id = ?", (storage_id,)
    ).fetchall()
    return [ServiceIdResult(name=vpath, role=role) for vpath, role in rows]


_SQLITE_VARIABLE_LIMIT = 999


def get_json_filenames_batch(
    db: sqlite3.Connection, vpaths: list[str]
) -> dict[str, str]:
    """Return a mapping of vpath -> json_filename for the given vpaths.

    Chunks the input to stay within SQLite's variable-number limit.
    """
    if not vpaths:
        return {}
    result: dict[str, str] = {}
    for i in range(0, len(vpaths), _SQLITE_VARIABLE_LIMIT):
        chunk = vpaths[i : i + _SQLITE_VARIABLE_LIMIT]
        placeholders = ",".join("?" * len(chunk))
        rows = db.execute(
            f"SELECT vpath, json_filename FROM files WHERE vpath IN ({placeholders})",
            chunk,
        ).fetchall()
        result.update(rows)
    return result


def get_vpaths_by_file_ids(
    db: sqlite3.Connection, file_ids: list[str]
) -> dict[str, str]:
    """Return a mapping of file_id -> vpath for the given file_ids only."""
    if not file_ids:
        return {}
    result: dict[str, str] = {}
    for i in range(0, len(file_ids), _SQLITE_VARIABLE_LIMIT):
        chunk = file_ids[i : i + _SQLITE_VARIABLE_LIMIT]
        placeholders = ",".join("?" * len(chunk))
        rows = db.execute(
            f"SELECT file_id, vpath FROM files WHERE file_id IN ({placeholders})",
            chunk,
        ).fetchall()
        result.update(rows)
    return result


class _ResolvedFile(NamedTuple):
    vpath: str
    meta: dict[str, Any]


def _resolve_and_load(
    name: str,
    *,
    db: sqlite3.Connection,
    index_dir: Path,
    cwd: str | None,
) -> _ResolvedFile:
    """Resolve a file name to a unique vpath and load its JSON metadata.

    Exits with code 1 if no match is found or the name is ambiguous.
    """
    stubs = (
        IndexEntry(name=vpath, storage_id="", meta={})
        for vpath, _ in _entries_under_db(db, (cwd + "/") if cwd else "")
    )
    matches = resolve_name(stubs, name)

    if len(matches) > 1:
        print(f"Error: ambiguous name '{name}', matches:", file=sys.stderr)
        for match in matches:
            print(f"  {match.name}", file=sys.stderr)
        sys.exit(1)

    vpath = matches[0].name
    json_filename = get_json_filename(db, vpath)
    if json_filename is None:
        print(f"Error: '{vpath}' not found in shell index", file=sys.stderr)
        sys.exit(1)

    with open(index_dir / json_filename, encoding="utf-8") as f:
        meta: dict[str, Any] = json.load(f)

    return _ResolvedFile(vpath=vpath, meta=meta)


class ShellIndexCollector:
    """Collects navigation metadata for SHELL_INDEX.db during archive creation."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db = sqlite3.connect(str(db_path))
        self._db.executescript(SHELL_DB_SCHEMA)
        self._db.execute("PRAGMA journal_mode=OFF")
        self._db.execute("PRAGMA synchronous=OFF")

    def add_file(
        self,
        vpath: str,
        file_id: str,
        json_filename: str,
        storage_ids: list[StorageEntry],
    ) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO files VALUES (?, ?, ?)",
            (vpath, json_filename, file_id),
        )
        for sid, role in storage_ids:
            self._db.execute(
                "INSERT OR REPLACE INTO storage VALUES (?, ?, ?)",
                (sid, vpath, role),
            )
        parts = [p for p in vpath.split("/") if p]
        for depth, part in enumerate(parts):
            parent = "/".join(parts[:depth])
            child = part + ("/" if depth < len(parts) - 1 else "")
            self._db.execute(
                "INSERT OR IGNORE INTO children VALUES (?, ?)", (parent, child)
            )
        self._db.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._db

    def stream_db(self) -> Iterator[bytes]:
        self._db.commit()
        self._db.close()
        with open(self._db_path, "rb") as f:
            while chunk := f.read(_DB_STREAM_CHUNK_SIZE):
                yield chunk
