#!/usr/bin/env python3
"""Archive format constants and standalone CLI for Loom archives.

``cli.py`` is bundled into every archive; requires only the Python stdlib. Run without
arguments for an interactive shell (prompt ``loom:/>``, TAB autocomplete, history
navigation), or pass a subcommand directly for scripting. Shell-only commands: ``cd``,
``pwd``, ``clear``. Type ``help`` inside the shell for a full command list. Exit codes:
0 success, 1 no results, 2 usage error.
"""

import argparse
import fnmatch
import json
import re
import shlex
import shutil
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, NamedTuple

_readline: ModuleType | None = None
try:
    import readline

    _readline = readline
except ImportError:
    pass

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
CLI_DOC: str = __doc__ or ""
SHELL_PROMPT = "loom:"
CLI_DESCRIPTION = "Loom archive CLI"
ERR_NO_FILE_FOUND = "no file found matching"

# ---------------------------------------------------------------------------
# CLI — data types
# ---------------------------------------------------------------------------


@dataclass
class IndexEntry:
    name: str
    storage_id: str
    meta: dict[str, Any]


class ServiceIdResult(NamedTuple):
    name: str
    role: str  # "file", "thumbnail", or "rendered:<name>"


# ---------------------------------------------------------------------------
# CLI — path setup
# ---------------------------------------------------------------------------

ARCHIVE_ROOT = Path(__file__).parent
FILES_INDEX = ARCHIVE_ROOT / FILES_INDEX_DIR
FILES = ARCHIVE_ROOT / FILES_DIR
SHELL_HISTORY_FILE = ARCHIVE_ROOT / ".loom_history"

# ---------------------------------------------------------------------------
# CLI — commands
# ---------------------------------------------------------------------------

_CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_MAX_GREP_PATTERN_LEN = 512


def _sanitize(s: str) -> str:
    """Replace terminal control characters with the Unicode replacement character."""
    return _CTRL_CHAR_RE.sub("\ufffd", s)


def load_entries(*, index_dir: Path = FILES_INDEX) -> Iterator[IndexEntry]:
    for meta_path in index_dir.glob("*.json"):
        try:
            with open(meta_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, RecursionError):
            continue

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
        print(f"Error: {ERR_NO_FILE_FOUND} '{name}'", file=sys.stderr)
        sys.exit(1)

    return matches


def format_path(path: Path) -> str:
    path = path.resolve()

    try:
        return str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _vpath(name: str) -> str:
    """Strip leading slashes from an entry name for virtual path comparison.

    Archive entries may be stored with leading slashes (e.g. ``//host/dir/file``).
    Virtual navigation is rooted at the first non-empty component, so we normalise
    before any prefix comparisons.
    """
    return name.lstrip("/")


def _entries_under(cwd: str, *, index_dir: Path = FILES_INDEX) -> list[IndexEntry]:
    """Return all index entries whose path falls under cwd (all entries when cwd is
    '')."""
    entries = list(load_entries(index_dir=index_dir))
    if not cwd:
        return entries
    prefix = cwd + "/"
    return [e for e in entries if _vpath(e.name).startswith(prefix)]


def _list_children(cwd: str, entries: list[IndexEntry]) -> list[str]:
    """Return the immediate children of cwd: bare filenames and virtual dir names (with
    '/')."""
    prefix = cwd + "/" if cwd else ""
    seen_dirs: set[str] = set()
    result: list[str] = []
    for entry in sorted(entries, key=lambda e: e.name):
        rel = _vpath(entry.name)[len(prefix) :]
        if "/" in rel:
            dir_name = rel.split("/")[0]
            if dir_name not in seen_dirs:
                seen_dirs.add(dir_name)
                result.append(dir_name + "/")
        elif rel:
            result.append(rel)
    return result


def _resolve_cwd(current: str, target: str) -> str:
    """Resolve a cd target against current cwd, normalising '..' components.

    Returns the new cwd as a bare string (no leading/trailing slash).
    """
    if target.startswith("/"):
        parts: list[str] = [p for p in target.split("/") if p]
    else:
        parts = [p for p in current.split("/") if p] + [
            p for p in target.split("/") if p
        ]

    result: list[str] = []
    for part in parts:
        if part == "..":
            if result:
                result.pop()
        elif part != ".":
            result.append(part)

    return "/".join(result)


def cmd_ls(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    if cwd is None:
        path = args.path if args.path is not None else "*"
        matches = resolve_name(load_entries(index_dir=index_dir), path)
        for entry in sorted(matches, key=lambda x: x.name):
            print(_sanitize(entry.name))
    else:
        entries = _entries_under(cwd, index_dir=index_dir)
        if args.path is None:
            for child in _list_children(cwd, entries):
                print(_sanitize(child))
        else:
            matches = resolve_name(entries, args.path)
            for entry in sorted(matches, key=lambda x: x.name):
                print(_sanitize(entry.name))


def cmd_extract(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    files_dir: Path = FILES,
    cwd: str | None = None,
) -> None:
    all_entries = (
        list(load_entries(index_dir=index_dir))
        if cwd is None
        else _entries_under(cwd, index_dir=index_dir)
    )
    all_names = {e.name for e in all_entries}

    if not args.members:
        initial_matches = list(all_entries)
    else:
        initial_matches = []
        for pattern in args.members:
            initial_matches.extend(resolve_name(all_entries, pattern))
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


def _iter_values(data: object, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{prefix}.{k}" if prefix else k
            yield from _iter_values(v, path)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            yield from _iter_values(v, f"{prefix}[{i}]")
    elif data is not None:
        yield (prefix, str(data))


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


def cmd_grep(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    flags = re.IGNORECASE if args.ignore_case else 0
    pattern = _compile_grep_pattern(args.pattern, flags)

    found = False

    for meta_path in sorted(index_dir.glob("*.json")):
        with open(meta_path, encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("full_name") or data.get("full_path") or data.get("short_name")
        if not name:
            continue
        if cwd and not _vpath(name).startswith(cwd + "/"):
            continue

        if args.files_with_matches:
            for _key_path, value in _iter_values(data):
                if pattern.search(value):
                    print(_sanitize(name))
                    found = True
                    break
        else:
            for key_path, value in _iter_values(data):
                for line in value.splitlines() or [value]:
                    if pattern.search(line):
                        print(f"{_sanitize(name)} [{key_path}]: {line}")
                        found = True

    if not found:
        sys.exit(1)


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
    cwd: str | None = None,
) -> None:
    source = (
        _entries_under(cwd, index_dir=index_dir)
        if cwd is not None
        else load_entries(index_dir=index_dir)
    )
    matches = resolve_name(source, args.name)

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


def cmd_id(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    file_ref = args.file_ref
    if file_ref.startswith(f"{FILES_DIR}/"):
        storage_id = file_ref[len(f"{FILES_DIR}/") :]
    else:
        storage_id = file_ref

    results = _find_by_service_id(storage_id, index_dir=index_dir)

    if cwd:
        results = [r for r in results if _vpath(r.name).startswith(cwd + "/")]

    if not results:
        print(f"Error: no file found with id '{storage_id}'", file=sys.stderr)
        sys.exit(1)

    for name, role in results:
        if role == "file":
            print(name)
        else:
            print(f"{name} ({role})")


def cmd_find(
    args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    source = (
        _entries_under(cwd, index_dir=index_dir)
        if cwd is not None
        else load_entries(index_dir=index_dir)
    )
    pattern: str | None = args.name if args.name is not None else args.iname
    case_insensitive = bool(args.iname)
    for entry in sorted(source, key=lambda e: e.name):
        basename = _vpath(entry.name).rstrip("/").rsplit("/", 1)[-1]
        if pattern is None or fnmatch.fnmatch(
            basename.lower() if case_insensitive else basename,
            pattern.lower() if case_insensitive else pattern,
        ):
            print(_sanitize(entry.name))


def cmd_tree(
    _args: argparse.Namespace,
    *,
    index_dir: Path = FILES_INDEX,
    cwd: str | None = None,
) -> None:
    entries = (
        _entries_under(cwd, index_dir=index_dir)
        if cwd is not None
        else load_entries(index_dir=index_dir)
    )

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
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    subparsers = parser.add_subparsers(dest="command", required=False)

    ls_parser = subparsers.add_parser(
        "ls",
        aliases=["list"],
        help="List files in the archive",
    )
    ls_parser.add_argument(
        "path",
        nargs="?",
        default=None,
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
        help="Files to extract (path, suffix, or glob pattern); omit to extract all",
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

    grep_parser = subparsers.add_parser(
        "grep",
        help="Search archive metadata using a regex pattern",
        description=(
            "Search archive metadata using a regex pattern. "
            "Prints 'name [field.path]: line' for every matching line in a metadata value. "
            "Use -l to list only filenames. Use -i for case-insensitive matching. "
            "Exits with code 1 when no matches are found."
        ),
    )
    grep_parser.add_argument(
        "pattern",
        help="Regex pattern to search for in metadata values",
    )
    grep_parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Case-insensitive matching",
    )
    grep_parser.add_argument(
        "-l",
        "--files-with-matches",
        action="store_true",
        help="Only print filenames of entries with at least one match",
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

    find_parser = subparsers.add_parser(
        "find",
        help="Find files by name pattern",
        description=(
            "Find files by name pattern. "
            "Without options lists all files under the current directory. "
            "Use -name or -iname to filter by filename glob pattern."
        ),
    )
    name_group = find_parser.add_mutually_exclusive_group()
    name_group.add_argument(
        "-name",
        metavar="PATTERN",
        default=None,
        help="Filter by filename glob pattern (case-sensitive)",
    )
    name_group.add_argument(
        "-iname",
        metavar="PATTERN",
        default=None,
        help="Filter by filename glob pattern (case-insensitive)",
    )

    cd_parser = subparsers.add_parser("cd", help="Change virtual directory")
    cd_parser.add_argument(
        "path",
        nargs="?",
        default="/",
        help="Directory to navigate to (default: /)",
    )

    subparsers.add_parser("pwd", help="Print current virtual directory")

    subparsers.add_parser("clear", help="Clear the terminal screen")

    subparsers.add_parser(
        "help",
        help="Show this help message",
    )

    subparsers.add_parser(
        "shell",
        help="Start an interactive shell (default when run with no arguments)",
    )

    return parser


def _dispatch(args: argparse.Namespace, *, cwd: str | None = None) -> None:
    if args.command in ("ls", "list"):
        cmd_ls(args, cwd=cwd)
    elif args.command in ("x", "extract"):
        cmd_extract(args, cwd=cwd)
    elif args.command == "grep":
        cmd_grep(args, cwd=cwd)
    elif args.command == "find":
        cmd_find(args, cwd=cwd)
    elif args.command == "info":
        cmd_info(args, cwd=cwd)
    elif args.command == "tree":
        cmd_tree(args, cwd=cwd)
    elif args.command == "id":
        cmd_id(args, cwd=cwd)


_SHELL_SPECIAL_RE = re.compile(r"([ \t\n\\\"'`$!#@&;|<>*()?[\]{}~])")


def _shell_escape(s: str) -> str:
    """Escape shell-special characters in s with a backslash."""
    return _SHELL_SPECIAL_RE.sub(r"\\\1", s)


def _shell_unescape(s: str) -> str:
    """Strip backslash escapes from a shell-escaped string."""
    return re.sub(r"\\(.)", r"\1", s)


_SHELL_COMMANDS = [  # keep in sync with build_parser(); exit/quit have no subcommand
    "ls",
    "cd",
    "pwd",
    "clear",
    "find",
    "grep",
    "info",
    "tree",
    "x",
    "extract",
    "id",
    "help",
    "exit",
    "quit",
]


class _ShellCompleter:
    """Readline tab-completer for the archive shell.

    ``get_completions`` accepts explicit parameters so it can be unit-tested without a
    live readline session.
    """

    def __init__(self, *, index_dir: Path = FILES_INDEX) -> None:
        self.cwd: str = ""
        self._index_dir = index_dir
        self._matches: list[str] = []

    def __call__(self, text: str, state: int) -> str | None:
        if state == 0:
            line = _readline.get_line_buffer() if _readline is not None else ""
            begidx = _readline.get_begidx() if _readline is not None else 0
            self._matches = self.get_completions(text, line, begidx)
        return self._matches[state] if state < len(self._matches) else None

    def get_completions(self, text: str, line: str, begidx: int) -> list[str]:
        before = line[:begidx].lstrip()
        if not before:
            return [c for c in _SHELL_COMMANDS if c.startswith(text)]
        cmd = before.split()[0]
        if cmd in ("cd", "ls", "list", "info", "x", "extract"):
            full_arg = self._full_path_arg(cmd, line, begidx, text)
            dirs_only = cmd == "cd"
            completions = self._complete_path(full_arg, dirs_only=dirs_only)
            strip = len(full_arg) - len(text)
            return [c[strip:] for c in completions if len(c) >= strip]
        return []

    @staticmethod
    def _full_path_arg(cmd: str, line: str, begidx: int, text: str) -> str:
        """Reconstruct the full path argument, preserving spaces split by readline."""
        # Locate command end by leading-whitespace position (not str.find, which
        # would match cmd inside a path component like "ls ls_docs/").
        leading = len(line) - len(line.lstrip())
        cmd_end = leading + len(cmd)
        return line[cmd_end : begidx + len(text)].lstrip()

    def _complete_path(self, text: str, *, dirs_only: bool) -> list[str]:
        if "/" in text:
            dir_part, partial = text.rsplit("/", 1)
            search_cwd = _resolve_cwd(self.cwd, _shell_unescape(dir_part))
            prefix = text[: len(text) - len(partial)]
        else:
            search_cwd = self.cwd
            partial = text
            prefix = ""
        partial_raw = _shell_unescape(partial)
        under = _entries_under(search_cwd, index_dir=self._index_dir)
        children = _list_children(search_cwd, under)
        candidates = [c for c in children if c.endswith("/")] if dirs_only else children
        return [
            prefix + _shell_escape(c) for c in candidates if c.startswith(partial_raw)
        ]


def _do_cd(cwd: str, target: str, *, index_dir: Path = FILES_INDEX) -> str:
    """Resolve a cd target and return the new cwd, or print an error and return
    current."""
    new_cwd = _resolve_cwd(cwd, target)
    # root always exists — skip the presence check when new_cwd is empty
    if new_cwd and not any(
        _vpath(e.name).startswith(new_cwd + "/")
        for e in load_entries(index_dir=index_dir)
    ):
        print(f"cd: no such directory: {target}", file=sys.stderr)
        return cwd
    return new_cwd


def _make_prompt(cwd: str) -> str:
    """Build the interactive shell prompt for the given virtual directory."""
    return f"{SHELL_PROMPT}{cwd or '/'}> "


def _shell_step(
    line: str,
    parser: argparse.ArgumentParser,
    cwd: str,
    *,
    index_dir: Path = FILES_INDEX,
) -> tuple[str, bool]:
    """Process one shell input line; return (new_cwd, should_break)."""
    if line in ("exit", "quit"):
        return cwd, True
    try:
        tokens = shlex.split(line)
        cmd_args = parser.parse_args(tokens)
    except (ValueError, SystemExit) as exc:
        if isinstance(exc, ValueError):
            print(f"Parse error: {exc}", file=sys.stderr)
        return cwd, False
    if cmd_args.command == "shell":
        print("Already in shell.", file=sys.stderr)
        return cwd, False
    if cmd_args.command in ("help", "pwd", "cd", "clear"):
        if cmd_args.command == "pwd":
            print(f"/{cwd}" if cwd else "/")
        elif cmd_args.command == "cd":
            cwd = _do_cd(cwd, cmd_args.path, index_dir=index_dir)
        elif cmd_args.command == "clear":
            print("\033[2J\033[H", end="", flush=True)
        else:
            parser.print_help()
        return cwd, False
    try:
        _dispatch(cmd_args, cwd=cwd)
    except SystemExit:
        # command errors (e.g. resolve_name calling sys.exit) should not kill the shell
        pass
    return cwd, False


def cmd_shell(_args: argparse.Namespace, *, index_dir: Path = FILES_INDEX) -> None:
    parser = build_parser()
    print("Loom archive shell. Type 'help' for available commands, 'exit' to quit.")
    completer = _ShellCompleter(index_dir=index_dir)
    if _readline is not None:
        try:
            _readline.read_history_file(SHELL_HISTORY_FILE)
        except FileNotFoundError:
            pass
        _readline.set_completer(completer)
        _readline.set_completer_delims(" \t\n")
        _readline.parse_and_bind("tab: complete")
    cwd: str = ""
    try:
        while True:
            try:
                line = input(_make_prompt(cwd)).strip()
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("^C")
                continue

            if not line:
                continue
            # input() auto-adds to history in TTY mode; only add manually in
            # pipe mode (tests) to avoid duplicates causing double up-arrow presses.
            if _readline is not None and not sys.stdin.isatty():
                _readline.add_history(line)
            cwd, should_break = _shell_step(line, parser, cwd, index_dir=index_dir)
            completer.cwd = cwd
            if should_break:
                break
    finally:
        if _readline is not None and not SHELL_HISTORY_FILE.is_symlink():
            try:
                _readline.write_history_file(SHELL_HISTORY_FILE)
            except OSError:
                pass


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None or args.command == "shell":
        cmd_shell(args)
        return

    if args.command == "help":
        parser.print_help()
        return

    _dispatch(args)


if __name__ == "__main__":
    main()
