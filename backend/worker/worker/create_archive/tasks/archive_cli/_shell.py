import argparse
import datetime
import json
import os
import re
import shlex
import sqlite3
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import NamedTuple, cast

from ._commands import _dispatch, build_parser
from ._constants import (
    FILES_INDEX,
    SHELL_CRASH_LOG_FILE,
    SHELL_HISTORY_FILE,
    SHELL_PROMPT,
)
from ._db import directory_exists, get_children, get_json_filename
from ._utils import _iter_values, resolve_cwd

# On Windows, add the vendored pyreadline3 to sys.path so that `import readline`
# below finds the bundled compatibility shim.
if os.name == "nt":
    _vendor_path = str(Path(__file__).parent / "vendor")
    if _vendor_path not in sys.path:
        sys.path.insert(0, _vendor_path)
    # pyreadline3's __init__.py sets __version__ via importlib.metadata, but
    # silently skips it when dist-info is absent (as in the archive vendor/).
    # rlmain.py then crashes accessing pyreadline3.__version__, so pre-import
    # the package and supply the attribute as a fallback before readline.py runs.
    try:
        import pyreadline3 as _pyreadline3_pkg

        if not hasattr(_pyreadline3_pkg, "__version__"):
            _pyreadline3_pkg.__version__ = "unknown"
    except ImportError:
        pass

_readline: ModuleType | None = None
try:
    import readline

    _readline = readline
except ImportError:
    if os.name == "nt":
        print(
            "Tip: install pyreadline3 for tab completion and history"
            " (pip install pyreadline3)",
            file=sys.stderr,
        )

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
    "history",
    "find",
    "grep",
    "info",
    "cat",
    "translate",
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
            # pyreadline3 on Windows can return 0 for get_begidx() when
            # completing an empty token (cursor after a trailing space).
            # Fall back to computing begidx from the line length, which is
            # always correct when the cursor is at the end of the line.
            if begidx == 0 and line:
                begidx = len(line) - len(text)
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
            try:
                if shlex.split(after_cmd):  # complete parseable token → field mode
                    return self._complete_field(line, cmd_end, begidx, text)
            except ValueError:
                pass  # unclosed quote → still typing the path
        if cmd == "translate":
            leading = len(line) - len(line.lstrip())
            cmd_end = leading + len(cmd)
            after_cmd = line[cmd_end:begidx]
            try:
                if shlex.split(after_cmd):  # file already typed → language mode
                    return self._complete_language(line, cmd_end, begidx, text)
            except ValueError:
                pass  # unclosed quote → still typing the path
        if cmd == "grep":
            file_arg = self._grep_file_arg(line, begidx, text)
            return (
                self._complete_path_arg(file_arg, text, dirs_only=False)
                if file_arg is not None
                else []
            )
        if cmd in ("cd", "ls", "list", "info", "cat", "translate", "x", "extract"):
            full_arg = self._full_path_arg(cmd, line, begidx, text)
            dirs_only = cmd == "cd"
            return self._complete_path_arg(full_arg, text, dirs_only=dirs_only)
        return []

    @staticmethod
    def _full_path_arg(cmd: str, line: str, begidx: int, text: str) -> str:
        """Reconstruct the full path argument, preserving spaces split by readline."""
        leading = len(line) - len(line.lstrip())
        cmd_end = leading + len(cmd)
        return line[cmd_end : begidx + len(text)].lstrip()

    @staticmethod
    def _grep_file_arg(line: str, begidx: int, text: str) -> str | None:
        """Return the current FILE arg being typed for grep, or None if before the
        pattern.

        Returns None when the cursor is still on the pattern position (no non-option
        token has been typed after 'grep' yet), suppressing file completion there.
        Returns the reconstructed path fragment (possibly empty) once the pattern has
        been provided, enabling file path completion for subsequent FILE arguments.
        """
        leading = len(line) - len(line.lstrip())
        before_words = line[leading:begidx].split()
        if len(before_words) < 2:
            return None
        # First non-option token after the command is the pattern
        pattern_word = next(
            (w for w in before_words[1:] if not w.startswith("-")),
            None,
        )
        if pattern_word is None:
            return None
        # Locate the pattern token in line (after the command) to find where FILE args start
        cmd_end = leading + len(before_words[0])
        pat_start = line.find(pattern_word, cmd_end)
        if pat_start == -1:
            return None
        pat_end = pat_start + len(pattern_word)
        return line[pat_end : begidx + len(text)].lstrip()

    def _load_meta_for_path(
        self, line: str, cmd_end: int, begidx: int
    ) -> dict[str, object] | None:
        raw = line[cmd_end:begidx].strip()
        try:
            tokens = shlex.split(raw)
            path_text = tokens[0] if tokens else ""
        except ValueError:
            path_text = shell_unescape(raw)
        vpath = resolve_cwd(self.cwd, path_text).lstrip("/")
        json_filename = get_json_filename(self._db, vpath)
        if json_filename is None:
            return None
        return json.loads((self._index_dir / json_filename).read_text(encoding="utf-8"))

    def _complete_field(
        self, line: str, cmd_end: int, begidx: int, text: str
    ) -> list[str]:
        meta = self._load_meta_for_path(line, cmd_end, begidx)
        if meta is None:
            return []
        return [kp for kp, _ in _iter_values(meta) if kp.startswith(text)]

    def _complete_language(
        self, line: str, cmd_end: int, begidx: int, text: str
    ) -> list[str]:
        meta = self._load_meta_for_path(line, cmd_end, begidx)
        if meta is None:
            return []
        translations = cast(list[dict[str, object]], meta.get("translations") or [])
        return [
            str(t["language"])
            for t in translations
            if isinstance(t.get("language"), str)
            and str(t["language"]).startswith(text)
        ]

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

    def _complete_path_unescaped(self, text: str, *, dirs_only: bool) -> list[str]:
        """Complete a path without shell-escaping, for use inside quoted arguments."""
        if "/" in text:
            dir_part, partial = text.rsplit("/", 1)
            search_cwd = resolve_cwd(self.cwd, dir_part)
            prefix = text[: len(text) - len(partial)]
        else:
            search_cwd = self.cwd
            partial = text
            prefix = ""
        children = get_children(self._db, search_cwd)
        candidates = [c for c in children if c.endswith("/")] if dirs_only else children
        return [prefix + c for c in candidates if c.startswith(partial)]

    def _complete_path_arg(
        self, path_arg: str, text: str, *, dirs_only: bool
    ) -> list[str]:
        """Resolve completions for path_arg, handling both normal and quoted modes.

        When path_arg starts with a quote character, completions are returned in quoted
        form with unescaped filenames. This correctly handles the case where readline
        has space-split a quoted path (text no longer starts with the quote), because
        quoted mode is detected solely from path_arg rather than text.
        """
        if path_arg and path_arg[0] in ('"', "'"):
            quote = path_arg[0]
            unquoted_arg = path_arg[1:]
            # effective_text is the portion of unquoted_arg that readline sees as the
            # current token. If readline has not yet space-split the quoted arg, text
            # still starts with the quote char; otherwise text is the raw suffix.
            effective_text = text[1:] if text.startswith(quote) else text
            completions = self._complete_path_unescaped(
                unquoted_arg, dirs_only=dirs_only
            )
            strip = len(unquoted_arg) - len(effective_text)
            if strip < 0:
                return []
            # Only prepend the quote when readline's current token still includes it.
            prefix = quote if text.startswith(quote) else ""
            result = []
            for c in completions:
                if len(c) < strip:
                    continue
                completion = prefix + c[strip:]
                # Mirror bash: add closing quote for files; directories end with /
                # and stay open so the user can continue typing the subpath.
                if not c.endswith("/"):
                    completion += quote
                result.append(completion)
            return result
        completions = self._complete_path(path_arg, dirs_only=dirs_only)
        strip = len(path_arg) - len(text)
        return [c[strip:] for c in completions if len(c) >= strip]


def _cmd_history() -> None:
    if _readline is None:
        return
    count = _readline.get_current_history_length()
    width = len(str(count))
    for i in range(1, count + 1):
        item = _readline.get_history_item(i)
        if item:
            print(f"{i:{width}}  {item}")


def _resolve_history_ref(line: str, *, _depth: int = 0) -> str | None:
    """Expand !N or !! to the referenced history entry, following chains.

    Mirrors bash behaviour: !! re-runs the previous entry; !N re-runs entry N.
    Chains are followed (e.g. !! -> !2 -> ls) up to a depth limit.
    Returns the final command string, or None on error (message already printed).
    """
    if _depth > 20:
        print("!: expansion loop detected", file=sys.stderr)
        return None
    if _readline is None:
        print("!: readline not available", file=sys.stderr)
        return None
    num = _readline.get_current_history_length() - 1 if line == "!!" else int(line[1:])
    item = _readline.get_history_item(num)
    if item is None:
        label = "!!" if line == "!!" else f"!{num}"
        print(f"{label}: event not found", file=sys.stderr)
        return None
    if item == "!!" or (item.startswith("!") and item[1:].isdigit()):
        return _resolve_history_ref(item, _depth=_depth + 1)
    print(item)
    return item


def _handle_shell_only_cmd(
    cmd_args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    cwd: str,
    *,
    db: sqlite3.Connection,
) -> str:
    if cmd_args.command == "pwd":
        print(f"/{cwd}" if cwd else "/")
    elif cmd_args.command == "cd":
        cwd = _do_cd(cwd, cmd_args.path, db=db)
    elif cmd_args.command == "clear":
        print("\033[2J\033[H", end="", flush=True)
    elif cmd_args.command == "history":
        _cmd_history()
    else:
        parser.print_help()
    return cwd


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


def _write_crash_log(
    crash_log_file: Path,
    command_line: str,
    exc: BaseException,
) -> None:
    """Append a crash report entry to crash_log_file."""
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    tb = traceback.format_exc()
    separator = "=" * 72
    entry = (
        f"\n{separator}\n"
        f"[{timestamp}] Command: {command_line}\n"
        f"Exception: {type(exc).__name__}: {exc}\n"
        f"{tb}"
        f"{separator}\n"
    )
    try:
        with crash_log_file.open("a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        pass  # Don't let a log-write failure hide the original error


def _shell_step(
    line: str,
    parser: argparse.ArgumentParser,
    cwd: str,
    *,
    db: sqlite3.Connection,
    crash_log_file: Path | None,
) -> _StepResult:
    """Process one shell input line; return (new_cwd, should_break)."""
    if line == "!!" or (line.startswith("!") and line[1:].isdigit()):
        resolved = _resolve_history_ref(line)
        if resolved is None:
            return _StepResult(cwd, False)
        line = resolved
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
    if cmd_args.command in ("help", "pwd", "cd", "clear", "history"):
        cwd = _handle_shell_only_cmd(cmd_args, parser, cwd, db=db)
        return _StepResult(cwd, False)
    try:
        _dispatch(cmd_args, db=db, cwd=cwd)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(
            f"Error: an unexpected error occurred.\n" f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        if crash_log_file is not None:
            _write_crash_log(crash_log_file, line, exc)
            print(
                f"Details written to: {crash_log_file}",
                file=sys.stderr,
            )
    return _StepResult(cwd, False)


def cmd_shell(
    _args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    index_dir: Path = FILES_INDEX,
    history_file: Path | None = SHELL_HISTORY_FILE,
    crash_log_file: Path | None = SHELL_CRASH_LOG_FILE,
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
            cwd, should_break = _shell_step(
                line, parser, cwd, db=db, crash_log_file=crash_log_file
            )
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
