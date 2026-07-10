import argparse
import fnmatch
import json
import shutil
import sqlite3
import sys
from pathlib import Path, PurePosixPath

from ._constants import FILES, FILES_INDEX, JSON_INDENT
from ._db import _entries_under_db, get_child_vpaths_under, get_json_filenames_batch
from ._resolve import resolve_name
from ._types import IndexEntry
from ._utils import _sanitize


def _build_skip_set(args: argparse.Namespace) -> frozenset[str]:
    """Build the set of metadata categories to skip during extraction."""
    return frozenset(
        s
        for flag, s in [
            (args.no_meta or args.no_thumbnails, "thumbnails"),
            (args.no_meta or args.no_rendered, "rendered"),
            (args.no_meta or args.no_index, "index"),
        ]
        if flag
    )


def _is_plain_id(service_id: str) -> bool:
    """Plain filename: non-empty, no path separators, not a dot-component."""
    return bool(service_id) and "/" not in service_id and service_id not in (".", "..")


def _extract_entry(
    entry: IndexEntry,
    dest: Path,
    *,
    files_dir: Path,
    skip: frozenset[str],
) -> None:
    rel_parts = PurePosixPath(entry.name.lstrip("/")).parts
    entry_dir = dest.joinpath(*rel_parts)
    try:
        entry_dir.resolve().relative_to(dest.resolve())
    except ValueError:
        print(f"Error: unsafe path in entry '{entry.name}'", file=sys.stderr)
        return
    entry_dir.mkdir(parents=True, exist_ok=True)

    if not _is_plain_id(entry.storage_id):
        print(f"Error: invalid storage_id in '{entry.name}'", file=sys.stderr)
        return
    src = files_dir / entry.storage_id
    if not src.exists():
        print(f"Error: raw file not found in archive: {src}", file=sys.stderr)
        sys.exit(1)
    shutil.copy2(src, entry_dir / rel_parts[-1])
    print(_sanitize(entry.name))

    if "thumbnails" not in skip:
        thumb_id = (entry.meta.get("thumbnail_data") or {}).get("service_id")
        if thumb_id and _is_plain_id(thumb_id) and (files_dir / thumb_id).exists():
            shutil.copy2(files_dir / thumb_id, entry_dir / "thumbnail.png")

    if "rendered" not in skip:
        for render_name, render_data in (entry.meta.get("rendered_file") or {}).items():
            render_id = (render_data or {}).get("service_id")
            if (
                render_id
                and _is_plain_id(render_id)
                and (files_dir / render_id).exists()
            ):
                ext = ".png" if "image" in render_name else ".pdf"
                shutil.copy2(
                    files_dir / render_id,
                    entry_dir / f"rendered-{render_name}{ext}",
                )

    if "index" not in skip:
        (entry_dir / "index.json").write_text(
            json.dumps(entry.meta, indent=JSON_INDENT), encoding="utf-8"
        )


def cmd_extract(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    files_dir: Path = FILES,
    cwd: str | None = None,
) -> None:
    cwd_prefix = cwd + "/" if cwd else ""

    if not args.members:
        initial_vpaths = [vpath for vpath, _ in _entries_under_db(db, cwd_prefix)]
    else:
        stubs = [
            IndexEntry(name=vpath, storage_id="", meta={})
            for vpath, _ in _entries_under_db(db, cwd_prefix)
        ]
        initial_vpaths = list(
            {e.name: None for pat in args.members for e in resolve_name(stubs, pat)}
        )

    seen: dict[str, None] = {}
    for vpath in initial_vpaths:
        seen[vpath] = None
        if not args.no_recursion:
            seen.update(dict.fromkeys(get_child_vpaths_under(db, vpath)))
    dest = Path(args.directory) if args.directory else Path.cwd()
    skip = _build_skip_set(args)
    json_filename_map = get_json_filenames_batch(db, list(seen))

    for vpath in seen:
        if args.exclude and any(fnmatch.fnmatch(vpath, pat) for pat in args.exclude):
            continue
        json_filename = json_filename_map.get(vpath)
        if json_filename is None:
            continue
        meta = json.loads((index_dir / json_filename).read_text(encoding="utf-8"))
        _extract_entry(
            IndexEntry(
                name=vpath,
                storage_id=(meta.get("storage_data") or {}).get("service_id", ""),
                meta=meta,
            ),
            dest,
            files_dir=files_dir,
            skip=skip,
        )
