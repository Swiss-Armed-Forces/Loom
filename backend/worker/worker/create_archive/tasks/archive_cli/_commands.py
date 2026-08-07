import argparse
import sqlite3

from ._cmd_extract import cmd_extract
from ._cmd_find import cmd_find
from ._cmd_grep import cmd_grep
from ._cmd_id import cmd_id
from ._cmd_info import cmd_info
from ._cmd_ls import cmd_ls
from ._cmd_translate import cmd_translate
from ._cmd_tree import cmd_tree
from ._constants import CLI_DESCRIPTION, CLI_ENTRYPOINT_FILENAME


def _dispatch(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    cwd: str | None = None,
) -> None:
    if args.command in ("ls", "list"):
        cmd_ls(args, db=db, cwd=cwd)
    elif args.command in ("x", "extract"):
        cmd_extract(args, db=db, cwd=cwd)
    elif args.command == "grep":
        cmd_grep(args, db=db, cwd=cwd)
    elif args.command == "find":
        cmd_find(args, db=db, cwd=cwd)
    elif args.command == "info":
        cmd_info(args, db=db, cwd=cwd)
    elif args.command == "cat":
        args.field = "content"
        args.json = False
        cmd_info(args, db=db, cwd=cwd)
    elif args.command == "translate":
        cmd_translate(args, db=db, cwd=cwd)
    elif args.command == "tree":
        cmd_tree(args, db=db, cwd=cwd)
    elif args.command == "id":
        cmd_id(args, db=db, cwd=cwd)


_SHELL_HELP_EPILOG = (
    "Shell builtins (interactive shell only)\n"
    "  cd [DIR]    Navigate the virtual directory tree\n"
    "  pwd         Print current virtual directory\n"
    "  clear       Clear the terminal screen\n"
    "  history     Show numbered command history\n"
    "  exit/quit   Leave the shell (Ctrl+D also works)\n"
    "\n"
    "History & line editing\n"
    "  Up/Down     Walk through command history\n"
    "  Ctrl+R      Reverse incremental search through history\n"
    "  Tab         Autocomplete commands, paths, and field names\n"
    "  Ctrl+A/E    Jump to start / end of line\n"
    "  Alt+B/F     Move backward / forward one word\n"
    "  Ctrl+W      Delete previous word\n"
    "  Ctrl+K      Delete to end of line\n"
    "  Ctrl+L      Clear the screen\n"
    "  !N          Re-run history entry N  (see: history)\n"
    "  !!          Re-run the last command\n"
    "\n"
    "Note: requires GNU readline (standard on Unix/macOS);"
    " on Windows, pyreadline3 is bundled automatically when installed on the archive server.\n"
    "\n"
    "Exit codes\n"
    "  0  success\n"
    "  1  no results found\n"
    "  2  usage / argument error"
)


def _non_negative_int(value: str) -> int:
    n = int(value)
    if n < 0:
        raise argparse.ArgumentTypeError(
            f"must be a non-negative integer, got {value!r}"
        )
    return n


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=CLI_ENTRYPOINT_FILENAME,
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_SHELL_HELP_EPILOG,
    )
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
    x_parser.add_argument(
        "--strip-components",
        type=_non_negative_int,
        default=0,
        metavar="N",
        help=(
            "Strip N leading path components from each entry before writing to disk. "
            "Entries with fewer than N components are skipped. "
            "Useful for shortening deep paths on Windows."
        ),
    )

    grep_parser = subparsers.add_parser(
        "grep",
        help="Search archive metadata using a regex pattern",
        description=(
            "Search archive metadata using a regex pattern. "
            "Prints 'name [field.path]: line' for every matching line in a metadata value. "
            "Use -l to list only filenames. Use -i for case-insensitive matching. "
            "Provide FILE arguments to restrict the search to specific files. "
            "Exits with code 1 when no matches are found."
        ),
    )
    grep_parser.add_argument(
        "pattern",
        help="Regex pattern to search for in metadata values",
    )
    grep_parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Files to search (path, suffix, or glob); searches all files if omitted",
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
        "field",
        nargs="?",
        default=None,
        help="Field to print (dot-path, e.g. content, metadata.author)",
    )
    info_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Print full metadata as JSON",
    )

    cat_parser = subparsers.add_parser(
        "cat",
        help="Print the text content of a file (alias for: info NAME content)",
    )
    cat_parser.add_argument(
        "name",
        help="Human-readable file name (full path, suffix, or glob pattern)",
    )

    translate_parser = subparsers.add_parser(
        "translate",
        help="Print a translation of a file",
        description=(
            "Print a stored translation of a file. "
            "Without LANGUAGE, lists the available language codes and their confidence scores. "
            "With LANGUAGE, prints the translated text for that language."
        ),
    )
    translate_parser.add_argument(
        "name",
        help="Human-readable file name (full path, suffix, or glob pattern)",
    )
    translate_parser.add_argument(
        "language",
        nargs="?",
        default=None,
        help="Language code to print (e.g. en, de, fr); omit to list available languages",
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

    subparsers.add_parser("history", help="Show command history")

    subparsers.add_parser(
        "help",
        help="Show this help message",
    )

    subparsers.add_parser(
        "shell",
        help="Start an interactive shell (default when run with no arguments)",
    )

    return parser
