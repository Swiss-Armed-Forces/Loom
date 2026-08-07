import argparse
import fnmatch
import json
import sqlite3
import sys
from pathlib import Path

from ._constants import FILES_INDEX
from ._db import _entries_under_db
from ._utils import _iter_values, _matches_field_prefix, _sanitize


def cmd_find(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    cwd_prefix = (cwd + "/") if cwd else ""
    pattern: str | None = args.name if args.name is not None else args.iname
    case_insensitive = bool(args.iname)
    attrs: list[str] = args.attr or []

    found = False
    for vpath, json_filename in _entries_under_db(db, cwd_prefix):
        basename = vpath.rstrip("/").rsplit("/", 1)[-1]
        if pattern is not None and not fnmatch.fnmatch(
            basename.lower() if case_insensitive else basename,
            pattern.lower() if case_insensitive else pattern,
        ):
            continue
        if attrs:
            with open(index_dir / json_filename, encoding="utf-8") as f:
                data = json.load(f)
            key_paths = {kp for kp, _ in _iter_values(data)}
            if not all(
                any(_matches_field_prefix(kp, attr) for kp in key_paths)
                for attr in attrs
            ):
                continue
        print(_sanitize(vpath))
        found = True

    if not found:
        sys.exit(1)
