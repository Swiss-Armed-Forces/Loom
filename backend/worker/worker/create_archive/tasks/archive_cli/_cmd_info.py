import argparse
import json
import sqlite3
import sys
from pathlib import Path

from ._constants import FILES, FILES_INDEX
from ._db import _resolve_and_load, get_vpaths_by_file_ids
from ._types import IndexEntry
from ._utils import (
    _collapse_field_ranges,
    _iter_values,
    _matches_field_prefix,
    format_path,
)


def _print_info(
    entry: IndexEntry,
    entries_by_id: dict[str, str],
    *,
    files_dir: Path = FILES,
) -> None:
    meta = entry.meta

    print(f"name:      {entry.name}")

    service_id = (meta.get("storage_data") or {}).get("service_id")
    if service_id:
        print(f"file:      {format_path(files_dir / service_id)}")

    thumbnail_id = (meta.get("thumbnail_data") or {}).get("service_id")
    if thumbnail_id:
        print(f"thumbnail: {format_path(files_dir / thumbnail_id)}")

    rendered = [
        (name, data["service_id"])
        for name, data in (meta.get("rendered_file") or {}).items()
        if data and data.get("service_id")
    ]
    if rendered:
        print("rendered:")
        for render_name, render_id in rendered:
            print(f"  {render_name}: {format_path(files_dir / render_id)}")

    attachments = meta.get("attachments") or []
    if attachments:
        print("attachments:")
        for attachment in attachments:
            name = (
                entries_by_id.get(attachment.get("id") or "")
                or attachment.get("name")
                or attachment.get("id")
                or ""
            )
            print(f"  {name}")

    fields = [key_path for key_path, _ in _iter_values(meta)]
    if fields:
        print("fields:")
        for field in _collapse_field_ranges(fields):
            print(f"  {field}")


def _handle_info_field(field: str, meta: object) -> None:
    """Print the value(s) for a specific metadata field path and exit."""
    matched = [
        (kp, v) for kp, v in _iter_values(meta) if _matches_field_prefix(kp, field)
    ]
    if not matched:
        print(f"Error: field '{field}' not found", file=sys.stderr)
        sys.exit(1)
    if len(matched) == 1 and matched[0][0] == field:
        print(matched[0][1])  # exact leaf — print value only
    else:
        for kp, v in matched:
            print(f"{kp}: {v}")  # sub-tree — print path: value pairs


def cmd_info(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    files_dir: Path = FILES,
    cwd: str | None = None,
) -> None:
    resolved = _resolve_and_load(args.name, db=db, index_dir=index_dir, cwd=cwd)
    meta = resolved.meta

    entry = IndexEntry(
        name=resolved.vpath,
        storage_id=(meta.get("storage_data") or {}).get("service_id", ""),
        meta=meta,
    )

    field = getattr(args, "field", None)
    if field is not None:
        _handle_info_field(field, meta)
        return

    if args.json:
        print(json.dumps(meta, indent=2))
        return

    entries_by_id = get_vpaths_by_file_ids(
        db, [a.get("id") for a in meta.get("attachments") or [] if a.get("id")]
    )
    _print_info(entry, entries_by_id, files_dir=files_dir)
