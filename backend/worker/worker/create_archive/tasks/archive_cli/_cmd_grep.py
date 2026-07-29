import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path

from ._constants import FILES_INDEX
from ._db import _entries_under_db, _FileEntry, get_json_filename
from ._resolve import resolve_name
from ._types import IndexEntry
from ._utils import _iter_values, _sanitize

_MAX_GREP_PATTERN_LEN = 512


def _compile_grep_pattern(raw: str, flags: int) -> re.Pattern[str]:
    """Validate and compile a grep regex pattern, exiting on error."""
    if len(raw) > _MAX_GREP_PATTERN_LEN:
        print(
            f"grep: pattern too long (>{_MAX_GREP_PATTERN_LEN} chars)", file=sys.stderr
        )
        sys.exit(2)
    try:
        return re.compile(raw, flags)
    except re.error as exc:
        print(f"grep: invalid pattern: {exc}", file=sys.stderr)
        sys.exit(2)


def _iter_target_entries(
    db: sqlite3.Connection, cwd_prefix: str, file_pats: list[str]
) -> Iterator[_FileEntry]:
    """Yield entries matching any of the given file patterns, without duplicates."""
    seen: set[str] = set()
    for pat in file_pats:
        stubs = (
            IndexEntry(name=e.vpath, storage_id="", meta={})
            for e in _entries_under_db(db, cwd_prefix)
        )
        for match in resolve_name(stubs, pat):
            if match.name not in seen:
                seen.add(match.name)
                json_fn = get_json_filename(db, match.name)
                if json_fn is not None:
                    yield _FileEntry(vpath=match.name, json_filename=json_fn)


def cmd_grep(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    pattern = _compile_grep_pattern(
        args.pattern, re.IGNORECASE if args.ignore_case else 0
    )

    found = False
    cwd_prefix = (cwd + "/") if cwd else ""

    for vpath, json_filename in (
        _iter_target_entries(db, cwd_prefix, args.files)
        if args.files
        else _entries_under_db(db, cwd_prefix)
    ):
        with open(index_dir / json_filename, encoding="utf-8") as f:
            data = json.load(f)

        if args.files_with_matches:
            for _key_path, value in _iter_values(data):
                if pattern.search(value):
                    print(_sanitize(vpath))
                    found = True
                    break
        else:
            for key_path, value in _iter_values(data):
                for line in value.splitlines() or [value]:
                    if pattern.search(line):
                        print(f"{_sanitize(vpath)} [{key_path}]: {line}")
                        found = True

    if not found:
        sys.exit(1)
