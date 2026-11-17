import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from ._color import print_error, stdout_colors
from ._constants import FILES_INDEX
from ._db import _entries_under_db, _FileEntry, get_json_filename
from ._resolve import resolve_name
from ._types import IndexEntry
from ._utils import _FieldValue, _iter_values, _matches_field_prefix, _sanitize

_MAX_GREP_PATTERN_LEN = 512


def _compile_grep_pattern(raw: str, flags: int) -> re.Pattern[str]:
    """Validate and compile a grep regex pattern, exiting on error."""
    if len(raw) > _MAX_GREP_PATTERN_LEN:
        print_error(f"grep: pattern too long (>{_MAX_GREP_PATTERN_LEN} chars)")
        sys.exit(2)
    try:
        return re.compile(raw, flags)
    except re.error as exc:
        print_error(f"grep: invalid pattern: {exc}")
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


class _GrepMatch(NamedTuple):
    key_path: str
    line: str


def _searched_values(data: object, fields: list[str]) -> Iterator[_FieldValue]:
    """Yield the metadata values the search covers, honouring any -f restriction."""
    return (
        value
        for value in _iter_values(data)
        if not fields or any(_matches_field_prefix(value.key_path, f) for f in fields)
    )


def _has_match(data: object, pattern: re.Pattern[str], fields: list[str]) -> bool:
    return any(pattern.search(value) for _, value in _searched_values(data, fields))


def _iter_matches(
    data: object, pattern: re.Pattern[str], fields: list[str]
) -> Iterator[_GrepMatch]:
    """Yield every matching line, with the field path it was found under."""
    for key_path, value in _searched_values(data, fields):
        for line in value.splitlines() or [value]:
            if pattern.search(line):
                yield _GrepMatch(key_path=key_path, line=line)


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

    colors = stdout_colors()
    found = False
    cwd_prefix = (cwd + "/") if cwd else ""
    fields: list[str] = args.field or []

    for vpath, json_filename in (
        _iter_target_entries(db, cwd_prefix, args.files)
        if args.files
        else _entries_under_db(db, cwd_prefix)
    ):
        data = json.loads((index_dir / json_filename).read_text(encoding="utf-8"))

        if args.files_with_matches:
            if _has_match(data, pattern, fields):
                print(colors.path(_sanitize(vpath)))
                found = True
        else:
            for key_path, line in _iter_matches(data, pattern, fields):
                print(
                    f"{colors.path(_sanitize(vpath))}"
                    f" [{colors.field(key_path)}]:"
                    f" {colors.highlight(pattern, line)}"
                )
                found = True

    if not found:
        sys.exit(1)
