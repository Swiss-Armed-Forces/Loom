"""ANSI colouring for the archive CLI.

Colour is applied to strings that have already passed through ``_sanitize``: that
function replaces every control character — the escape character among them — so
metadata stored in an archive cannot reach the terminal as an escape sequence. The
sequences written here are the only ones the CLI emits.
"""

import ctypes
import json
import os
import re
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from ._constants import JSON_INDENT

COLOR_AUTO = "auto"
COLOR_ALWAYS = "always"
COLOR_NEVER = "never"
COLOR_CHOICES = (COLOR_AUTO, COLOR_ALWAYS, COLOR_NEVER)

COLOR_HELP = (
    "Colourise output: 'auto' (default) colours only when writing to a terminal,"
    " 'always' colours even through a pipe, 'never' disables colour."
    " NO_COLOR or TERM=dumb in the environment also disables it."
)

_RESET = "\033[0m"

_DIRECTORY = "1;34"
_MATCH = "1;31"
_FIELD = "36"
_ERROR = "1;31"
_PROMPT = "1;32"
_JSON_KEY = "34"
_JSON_STRING = "32"
_JSON_LITERAL = "33"

# Tokens of json.dumps output: an object key with its colon, any other string, and
# the bare literals. Strings are matched with their escapes so a quote inside one
# does not end the token.
_JSON_TOKEN_RE = re.compile(
    r'(?P<key>"(?:[^"\\]|\\.)*")(?P<colon>\s*:)'
    r'|"(?:[^"\\]|\\.)*"'
    r"|\b(?:true|false|null)\b"
    r"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
)

# Windows consoles render SGR sequences only while this console mode is set.
_WINDOWS_VT_FLAG = 0x0004
_WINDOWS_STD_HANDLE_BY_FD = {1: -11, 2: -12}


def _stream_fileno(stream: TextIO) -> int | None:
    try:
        return stream.fileno()
    except (AttributeError, OSError, ValueError):
        return None


def _is_tty(stream: TextIO) -> bool:
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _enable_windows_vt(kernel32: Any, handle_id: int) -> bool:
    """Set VT processing on a Windows standard handle, reporting whether it holds."""
    kernel32.GetStdHandle.restype = ctypes.c_void_p
    kernel32.GetStdHandle.argtypes = [ctypes.c_uint32]
    handle = kernel32.GetStdHandle(handle_id)
    if handle is None:
        return False

    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(ctypes.c_void_p(handle), ctypes.byref(mode)):
        return False  # a redirected handle is not a console
    if mode.value & _WINDOWS_VT_FLAG:
        return True
    return bool(
        kernel32.SetConsoleMode(ctypes.c_void_p(handle), mode.value | _WINDOWS_VT_FLAG)
    )


def _prepare_console(stream: TextIO) -> bool:
    """Return whether stream can render SGR sequences, enabling VT mode on Windows."""
    if sys.platform != "win32":
        return True

    handle_id = _WINDOWS_STD_HANDLE_BY_FD.get(_stream_fileno(stream) or -1)
    if handle_id is None:
        return False

    # ctypes.windll is defined on Windows alone.
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return False
    return _enable_windows_vt(windll.kernel32, handle_id)


def should_colorize(
    when: str | None, *, stream: TextIO, env: Mapping[str, str]
) -> bool:
    """Decide whether stream may carry SGR sequences under the given colour mode."""
    if when == COLOR_NEVER:
        return False
    if when == COLOR_ALWAYS:
        _prepare_console(stream)
        return True
    if env.get("NO_COLOR"):
        return False
    if env.get("TERM") == "dumb":
        return False
    if not _is_tty(stream):
        return False
    return _prepare_console(stream)


class Colors:
    """Wraps text in SGR sequences, or hands it back untouched when colour is off."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _paint(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}{_RESET}" if self.enabled else text

    def directory(self, text: str) -> str:
        return self._paint(text, _DIRECTORY)

    def field(self, text: str) -> str:
        return self._paint(text, _FIELD)

    def match(self, text: str) -> str:
        return self._paint(text, _MATCH)

    def error(self, text: str) -> str:
        return self._paint(text, _ERROR)

    def path(self, vpath: str) -> str:
        """Colour the directory components of a virtual path, leaving the name plain."""
        head, sep, tail = vpath.rpartition("/")
        if not sep:
            return vpath
        return self.directory(head + sep) + tail

    def entry(self, child_name: str) -> str:
        """Colour one directory listing entry; a directory carries a trailing slash."""
        return self.directory(child_name) if child_name.endswith("/") else child_name

    def highlight(self, pattern: re.Pattern[str], text: str) -> str:
        """Colour every non-empty match of pattern within text."""
        if not self.enabled:
            return text
        return pattern.sub(lambda m: self.match(m.group(0)) if m.group(0) else "", text)

    def json_text(self, data: object) -> str:
        """Render data as indented JSON, colouring keys, strings and literals."""
        text = json.dumps(data, indent=JSON_INDENT)
        if not self.enabled:
            return text
        return _JSON_TOKEN_RE.sub(self._paint_json_token, text)

    def _paint_json_token(self, token_match: re.Match[str]) -> str:
        colon = token_match.group("colon")
        if colon is not None:
            return self._paint(token_match.group("key"), _JSON_KEY) + colon
        token = token_match.group(0)
        style = _JSON_STRING if token.startswith('"') else _JSON_LITERAL
        return self._paint(token, style)

    def prompt(self, text: str) -> str:
        """Colour a readline prompt, bracketing the sequences as non-printing.

        readline counts every byte of a prompt towards the cursor column unless the non-
        printing runs are delimited by \\001 and \\002, and a miscounted prompt corrupts
        editing and history recall on wrapped lines.
        """
        if not self.enabled:
            return text
        return f"\001\033[{_PROMPT}m\002{text}\001{_RESET}\002"


class _ColorState:
    """The colour mode in force, resolved against whichever stream is written to."""

    def __init__(self) -> None:
        self.mode: str = COLOR_AUTO

    def colors_for(self, stream: TextIO) -> Colors:
        return Colors(should_colorize(self.mode, stream=stream, env=os.environ))


_STATE = _ColorState()


def set_color_mode(when: str | None) -> None:
    """Set the colour mode for subsequent output; None means 'auto'."""
    _STATE.mode = when or COLOR_AUTO


def color_mode() -> str:
    """Return the colour mode in force."""
    return _STATE.mode


def stdout_colors() -> Colors:
    return _STATE.colors_for(sys.stdout)


def stderr_colors() -> Colors:
    return _STATE.colors_for(sys.stderr)


def print_error(message: str) -> None:
    """Print a message to stderr in the error style."""
    print(stderr_colors().error(message), file=sys.stderr)
