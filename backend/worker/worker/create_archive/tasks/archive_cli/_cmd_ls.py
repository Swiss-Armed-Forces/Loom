import argparse
import sqlite3

from ._db import _entries_under_db, get_children
from ._resolve import resolve_name
from ._types import IndexEntry
from ._utils import _sanitize


def cmd_ls(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    cwd: str | None = None,
) -> None:
    if cwd is None:
        # Standalone mode: list all or filtered
        path = args.path if args.path is not None else "*"
        stubs = (
            IndexEntry(name=vpath, storage_id="", meta={})
            for vpath, _ in _entries_under_db(db, "")
        )
        matches = resolve_name(stubs, path)
        for entry in sorted(matches, key=lambda x: x.name):
            print(_sanitize(entry.name))
    else:
        if args.path is None:
            # Shell mode, no path: fast lookup from children table
            for child in get_children(db, cwd):
                print(_sanitize(child))
        else:
            cwd_prefix = cwd + "/" if cwd else ""
            stubs = (
                IndexEntry(name=vpath, storage_id="", meta={})
                for vpath, _ in _entries_under_db(db, cwd_prefix)
            )
            matches = resolve_name(stubs, args.path)
            for entry in sorted(matches, key=lambda x: x.name):
                print(_sanitize(entry.name))
