#!/usr/bin/env python3
"""Archive format constants and standalone CLI for Loom archives.

This module doubles as a runnable CLI script: it is bundled into every archive as
``cli.py`` so that users can interact with extracted archives without needing any
additional tooling beyond a standard Python installation.
"""

import argparse
import fnmatch
import json
import shutil
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Archive format constants (imported by compress / unzip tasks)
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "MANIFEST.json"
README_FILENAME = "README.md"
CLI_FILENAME = "cli.py"
FILES_DIR = "files"
FILES_INDEX_DIR = "files_index"
JSON_SUFFIX = ".json"
ZIP_EXTENSION = ".zip"
JSON_INDENT = 2

# ---------------------------------------------------------------------------
# CLI — data types
# ---------------------------------------------------------------------------


@dataclass
class IndexEntry:
    name: str
    storage_id: str
    meta: dict


class ServiceIdResult(NamedTuple):
    name: str
    role: str  # "file", "thumbnail", or "rendered:<name>"


# ---------------------------------------------------------------------------
# CLI — path setup
# ---------------------------------------------------------------------------

ARCHIVE_ROOT = Path(__file__).parent
FILES_INDEX = ARCHIVE_ROOT / FILES_INDEX_DIR
FILES = ARCHIVE_ROOT / FILES_DIR

# ---------------------------------------------------------------------------
# CLI — commands
# ---------------------------------------------------------------------------


def load_entries(*, index_dir: Path = FILES_INDEX) -> Iterator[IndexEntry]:
    for meta_path in index_dir.glob("*.json"):
        with open(meta_path, encoding="utf-8") as f:
            data = json.load(f)

        storage_id: str | None = (data.get("storage_data") or {}).get("service_id")
        full_name: str | None = (
            data.get("full_name") or data.get("full_path") or data.get("short_name")
        )

        if full_name and storage_id:
            yield IndexEntry(name=full_name, storage_id=storage_id, meta=data)


def resolve_name(
    entries: Iterable[IndexEntry], name: str, *, wildcards: bool = True
) -> list[IndexEntry]:
    exact: list[IndexEntry] = []
    suffix: list[IndexEntry] = []
    prefix: list[IndexEntry] = []
    glob_matches: list[IndexEntry] = []

    for e in entries:
        if e.name == name:
            exact.append(e)
        elif e.name.endswith(name):
            suffix.append(e)
        elif name.endswith("/") and e.name.startswith(name):
            prefix.append(e)
        elif wildcards and fnmatch.fnmatch(e.name, name):
            glob_matches.append(e)

    matches = exact or suffix or prefix or glob_matches

    if not matches:
        print(f"Error: no file found matching '{name}'", file=sys.stderr)
        sys.exit(1)

    return matches


def format_path(path: Path) -> str:
    path = path.resolve()

    try:
        return str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def cmd_ls(args: argparse.Namespace, *, index_dir: Path = FILES_INDEX) -> None:
    matches = resolve_name(load_entries(index_dir=index_dir), args.path)

    for entry in sorted(matches, key=lambda x: x.name):
        print(entry.name)


def cmd_extract(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    files_dir: Path = FILES,
) -> None:
    all_entries = list(load_entries(index_dir=index_dir))
    all_names = {e.name for e in all_entries}

    if not args.members:
        initial_matches = list(all_entries)
    else:
        initial_matches = []
        for pattern in args.members:
            initial_matches.extend(
                resolve_name(all_entries, pattern, wildcards=args.wildcards)
            )
        initial_matches = list({e.name: e for e in initial_matches}.values())

    final_matches: list[IndexEntry] = []
    for entry in initial_matches:
        is_dir_like = any(n.startswith(entry.name + "/") for n in all_names)
        if is_dir_like and not args.no_recursion:
            final_matches.append(entry)
            final_matches.extend(
                e for e in all_entries if e.name.startswith(entry.name + "/")
            )
        else:
            final_matches.append(entry)

    deduped = list({e.name: e for e in final_matches}.values())

    if args.exclude:
        deduped = [
            e
            for e in deduped
            if not any(fnmatch.fnmatch(e.name, pat) for pat in args.exclude)
        ]

    dest = Path(args.directory) if args.directory else Path.cwd()

    skip: frozenset[str] = frozenset(
        s
        for flag, s in [
            (args.no_meta or args.no_thumbnails, "thumbnails"),
            (args.no_meta or args.no_rendered, "rendered"),
            (args.no_meta or args.no_index, "index"),
        ]
        if flag
    )

    for entry in deduped:
        _extract_entry(entry, dest, files_dir=files_dir, skip=skip)


def _extract_entry(
    entry: IndexEntry,
    dest: Path,
    *,
    files_dir: Path,
    skip: frozenset[str],
) -> None:
    rel_parts = PurePosixPath(entry.name.lstrip("/")).parts
    entry_dir = dest.joinpath(*rel_parts)
    entry_dir.mkdir(parents=True, exist_ok=True)

    src = files_dir / entry.storage_id
    if not src.exists():
        print(f"Error: raw file not found in archive: {src}", file=sys.stderr)
        sys.exit(1)
    shutil.copy2(src, entry_dir / rel_parts[-1])
    print(entry.name)

    if "thumbnails" not in skip:
        thumb_id = (entry.meta.get("thumbnail_data") or {}).get("service_id")
        if thumb_id and (files_dir / thumb_id).exists():
            shutil.copy2(files_dir / thumb_id, entry_dir / "thumbnail.png")

    if "rendered" not in skip:
        for render_name, render_data in (entry.meta.get("rendered_file") or {}).items():
            render_id = (render_data or {}).get("service_id")
            if render_id and (files_dir / render_id).exists():
                ext = ".png" if "image" in render_name else ".pdf"
                shutil.copy2(
                    files_dir / render_id,
                    entry_dir / f"rendered-{render_name}{ext}",
                )

    if "index" not in skip:
        (entry_dir / "index.json").write_text(
            json.dumps(entry.meta, indent=JSON_INDENT), encoding="utf-8"
        )


def cmd_search(args: argparse.Namespace, *, index_dir: Path = FILES_INDEX) -> None:
    query = args.query.lower()
    results: list[str] = []

    for meta_path in index_dir.glob("*.json"):
        raw = meta_path.read_text()

        if query in raw.lower():
            data = json.loads(raw)
            name = (
                data.get("full_name") or data.get("full_path") or data.get("short_name")
            )

            if name:
                results.append(name)

    found = bool(results)

    for name in sorted(results):
        print(name)

    if not found:
        print(f"No results for '{args.query}'")


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
            name = entries_by_id.get(attachment["id"]) or attachment["name"]
            print(f"  {name}")


def cmd_info(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    files_dir: Path = FILES,
) -> None:
    matches = resolve_name(load_entries(index_dir=index_dir), args.name)

    if len(matches) > 1:
        print(f"Error: ambiguous name '{args.name}', matches:", file=sys.stderr)
        for match in matches:
            print(f"  {match.name}", file=sys.stderr)
        sys.exit(1)

    entry = matches[0]

    if args.json:
        print(json.dumps(entry.meta, indent=2))
        return

    entries_by_id: dict[str, str] = {
        e.meta["id_"]: e.name
        for e in load_entries(index_dir=index_dir)
        if "id_" in e.meta
    }
    _print_info(entry, entries_by_id, files_dir=files_dir)


def _find_by_service_id(
    storage_id: str, *, index_dir: Path = FILES_INDEX
) -> list[ServiceIdResult]:
    """Search all index entries for a service_id across storage, thumbnail, and rendered
    files."""
    results: list[ServiceIdResult] = []
    for meta_path in index_dir.glob("*.json"):
        with open(meta_path, encoding="utf-8") as f:
            data = json.load(f)

        name: str | None = (
            data.get("full_name") or data.get("full_path") or data.get("short_name")
        )
        if not name:
            continue

        if (data.get("storage_data") or {}).get("service_id") == storage_id:
            results.append(ServiceIdResult(name=name, role="file"))

        if (data.get("thumbnail_data") or {}).get("service_id") == storage_id:
            results.append(ServiceIdResult(name=name, role="thumbnail"))

        for render_name, render_data in (data.get("rendered_file") or {}).items():
            if (render_data or {}).get("service_id") == storage_id:
                results.append(
                    ServiceIdResult(name=name, role=f"rendered:{render_name}")
                )

    return results


def cmd_id(args: argparse.Namespace, *, index_dir: Path = FILES_INDEX) -> None:
    file_ref = args.file_ref
    if file_ref.startswith(f"{FILES_DIR}/"):
        storage_id = file_ref[len(f"{FILES_DIR}/") :]
    else:
        storage_id = file_ref

    results = _find_by_service_id(storage_id, index_dir=index_dir)

    if not results:
        print(f"Error: no file found with id '{storage_id}'", file=sys.stderr)
        sys.exit(1)

    for name, role in results:
        if role == "file":
            print(name)
        else:
            print(f"{name} ({role})")


def cmd_tree(_args: argparse.Namespace, *, index_dir: Path = FILES_INDEX) -> None:
    entries = load_entries(index_dir=index_dir)

    tree: dict = {}

    for entry in entries:
        parts = [p for p in entry.name.replace("\\", "/").split("/") if p]

        if not parts:
            continue

        node = tree

        for part in parts[:-1]:
            if node.get(part) is None:
                node[part] = {}

            node = node[part]

        if parts[-1] not in node:
            node[parts[-1]] = None

    def print_tree(node: dict, prefix: str = "") -> None:
        items = sorted(node.keys())

        for i, key in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "

            print(prefix + connector + key)

            if isinstance(node[key], dict):
                extension = "    " if i == len(items) - 1 else "│   "
                print_tree(node[key], prefix + extension)

    print_tree(tree)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Loom archive CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ls_parser = subparsers.add_parser(
        "ls",
        aliases=["list"],
        help="List files in the archive",
    )
    ls_parser.add_argument(
        "path",
        nargs="?",
        default="*",
        help="Optional path, suffix, or glob pattern",
    )

    x_parser = subparsers.add_parser(
        "x",
        aliases=["extract"],
        help="Extract file(s) from the archive",
    )
    x_parser.add_argument(
        "members",
        nargs="*",
        metavar="MEMBER",
        help="Files to extract (path, suffix, or glob if --wildcards); omit to extract all",
    )
    x_parser.add_argument(
        "-C",
        "--directory",
        default=None,
        metavar="DIR",
        help="Change to DIR before extracting (default: current directory)",
    )
    x_parser.add_argument(
        "--no-recursion",
        action="store_true",
        help="Do not descend into directories (recursion is on by default)",
    )
    x_parser.add_argument(
        "--wildcards",
        action="store_true",
        help="Use glob wildcards when matching member patterns",
    )
    x_parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Exclude files matching PATTERN (glob); repeatable",
    )
    x_parser.add_argument(
        "--no-thumbnails",
        action="store_true",
        help="Do not extract thumbnails",
    )
    x_parser.add_argument(
        "--no-rendered",
        action="store_true",
        help="Do not extract rendered file variants",
    )
    x_parser.add_argument(
        "--no-index",
        action="store_true",
        help="Do not extract index.json metadata",
    )
    x_parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Do not extract any metadata (thumbnails, rendered, index.json)",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search files in the index",
    )
    search_parser.add_argument(
        "query",
        help="Search string",
    )

    info_parser = subparsers.add_parser(
        "info",
        help="Show information about a file",
    )
    info_parser.add_argument(
        "name",
        help="Human-readable file name (full path, suffix, or glob pattern)",
    )
    info_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Print full metadata as JSON",
    )

    subparsers.add_parser(
        "tree",
        help="Display archive files as a directory tree",
    )

    id_parser = subparsers.add_parser(
        "id",
        help="Resolve a files/{id} path to its human-readable name",
    )
    id_parser.add_argument(
        "file_ref",
        help="File reference as files/{id} or just {id}",
    )

    subparsers.add_parser(
        "help",
        help="Show this help message",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        return

    if args.command in ("ls", "list"):
        cmd_ls(args)
    elif args.command in ("x", "extract"):
        cmd_extract(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "tree":
        cmd_tree(args)
    elif args.command == "id":
        cmd_id(args)


if __name__ == "__main__":
    main()
