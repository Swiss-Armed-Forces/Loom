import argparse
import json
import re
import shlex
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

from ._commands import _dispatch, build_parser
from ._constants import FILES_INDEX, SHELL_HISTORY_FILE, SHELL_PROMPT
from ._db import directory_exists, get_children, get_json_filename
from ._utils import _iter_values, resolve_cwd

_readline: ModuleType | None = None
try:
    import readline

    _readline = readline
except ImportError:
    pass

_SHELL_SPECIAL_RE = re.compile(r"([ \t\n\\\"'`$!#@&;|<>*()?[\]{}~])")


def shell_escape(s: str) -> str:
    """Escape shell-special characters in s with a backslash."""
    return _SHELL_SPECIAL_RE.sub(r"\\\1", s)


def shell_unescape(s: str) -> str:
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


class ShellCompleter:
    """Readline tab-completer for the archive shell.

    ``get_completions`` accepts explicit parameters so it can be unit-tested without a
    live readline session.
    """

    def __init__(
        self, *, db: sqlite3.Connection, index_dir: Path = FILES_INDEX
    ) -> None:
        self.cwd: str = ""
        self._db = db
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
        if cmd == "info":
            leading = len(line) - len(line.lstrip())
            cmd_end = leading + len(cmd)
            after_cmd = line[cmd_end:begidx]
            if after_cmd.strip():  # path already provided → complete field name
                return self._complete_field(line, cmd_end, begidx, text)
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
        leading = len(line) - len(line.lstrip())
        cmd_end = leading + len(cmd)
        return line[cmd_end : begidx + len(text)].lstrip()

    def _complete_field(
        self, line: str, cmd_end: int, begidx: int, text: str
    ) -> list[str]:
        path_text = shell_unescape(line[cmd_end:begidx].strip())
        vpath = resolve_cwd(self.cwd, path_text).lstrip("/")
        json_filename = get_json_filename(self._db, vpath)
        if json_filename is None:
            return []
        meta = json.loads((self._index_dir / json_filename).read_text(encoding="utf-8"))
        return [kp for kp, _ in _iter_values(meta) if kp.startswith(text)]

    def _complete_path(self, text: str, *, dirs_only: bool) -> list[str]:
        if "/" in text:
            dir_part, partial = text.rsplit("/", 1)
            search_cwd = resolve_cwd(self.cwd, shell_unescape(dir_part))
            prefix = text[: len(text) - len(partial)]
        else:
            search_cwd = self.cwd
            partial = text
            prefix = ""
        partial_raw = shell_unescape(partial)
        children = get_children(self._db, search_cwd)
        candidates = [c for c in children if c.endswith("/")] if dirs_only else children
        return [
            prefix + shell_escape(c) for c in candidates if c.startswith(partial_raw)
        ]


def _do_cd(cwd: str, target: str, *, db: sqlite3.Connection) -> str:
    new_cwd = resolve_cwd(cwd, target)
    # root always exists — skip the presence check when new_cwd is empty
    if new_cwd and not directory_exists(db, new_cwd):
        print(f"cd: no such directory: {target}", file=sys.stderr)
        return cwd
    return new_cwd


def _make_prompt(cwd: str) -> str:
    return f"{SHELL_PROMPT}{cwd or '/'}> "


class _StepResult(NamedTuple):
    cwd: str
    should_break: bool


def _shell_step(
    line: str,
    parser: argparse.ArgumentParser,
    cwd: str,
    *,
    db: sqlite3.Connection,
) -> _StepResult:
    """Process one shell input line; return (new_cwd, should_break)."""
    if line in ("exit", "quit"):
        return _StepResult(cwd, True)
    try:
        tokens = shlex.split(line)
        cmd_args = parser.parse_args(tokens)
    except (ValueError, SystemExit) as exc:
        if isinstance(exc, ValueError):
            print(f"Parse error: {exc}", file=sys.stderr)
        return _StepResult(cwd, False)
    if cmd_args.command == "shell":
        print("Already in shell.", file=sys.stderr)
        return _StepResult(cwd, False)
    if cmd_args.command in ("help", "pwd", "cd", "clear"):
        if cmd_args.command == "pwd":
            print(f"/{cwd}" if cwd else "/")
        elif cmd_args.command == "cd":
            cwd = _do_cd(cwd, cmd_args.path, db=db)
        elif cmd_args.command == "clear":
            print("\033[2J\033[H", end="", flush=True)
        else:
            parser.print_help()
        return _StepResult(cwd, False)
    try:
        _dispatch(cmd_args, db=db, cwd=cwd)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print()
    return _StepResult(cwd, False)


def cmd_shell(
    _args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    history_file: Path | None = SHELL_HISTORY_FILE,
    input_fn: Callable[[str], str] = input,
) -> None:
    parser = build_parser()
    print("Loom archive shell. Type 'help' for available commands, 'exit' to quit.")
    completer = ShellCompleter(db=db, index_dir=index_dir)
    if _readline is not None:
        if history_file is not None:
            try:
                _readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
        _readline.set_completer(completer)
        _readline.set_completer_delims(" \t\n")
        _readline.parse_and_bind("tab: complete")
    cwd: str = ""
    try:
        while True:
            try:
                line = input_fn(_make_prompt(cwd)).strip()
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
            cwd, should_break = _shell_step(line, parser, cwd, db=db)
            completer.cwd = cwd
            if should_break:
                break
    finally:
        if (
            _readline is not None
            and history_file is not None
            and not history_file.is_symlink()
        ):
            try:
                _readline.write_history_file(history_file)
            except OSError:
                pass
