import argparse
import fnmatch
import sqlite3

from ._db import _entries_under_db
from ._utils import _sanitize


def cmd_find(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    cwd: str | None = None,
) -> None:
    cwd_prefix = (cwd + "/") if cwd else ""
    pattern: str | None = args.name if args.name is not None else args.iname
    case_insensitive = bool(args.iname)
    for vpath, _ in _entries_under_db(db, cwd_prefix):
        basename = vpath.rstrip("/").rsplit("/", 1)[-1]
        if pattern is None or fnmatch.fnmatch(
            basename.lower() if case_insensitive else basename,
            pattern.lower() if case_insensitive else pattern,
        ):
            print(_sanitize(vpath))
