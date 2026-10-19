"""Everything the operator sees.

The screen this draws on is a Linux VT that systemd started on a `TTYPath`
(installer.nix), which means three things that shape the whole module:

  * There is no `TERM`, and no shell to have set `COLUMNS`. Rich asks the kernel
    for the window size through an ioctl on the file descriptor, which needs
    neither -- but the colour system has to be pinned, because with `TERM` unset
    rich would otherwise assume 256 colours on a console that has 16.
  * There is no locale either, so the stream is deliberately put into ASCII with
    `errors="replace"`. That is not a limitation worked around: the VT font
    (branding.nix) carries about 515 glyphs and is checked at build time for
    exactly four of them, none of which are box drawing or rich's half-block
    progress bar. Rich picks its ASCII renderings off the stream encoding, so
    pinning the encoding is what makes every frame drawable -- and nothing the
    installer prints can raise UnicodeEncodeError onto a console in the field.
  * Off a terminal -- `loom-install 2>install.log`, or the unit's output in the
    journal -- everything collapses to plain text, so escapes never reach a log.

The one thing rich is not used for is the mark: `loom-eyes` (branding.nix) draws
it, because the installed box prints the same pair in its login banner and two
copies would drift.
"""

import io
import os
import select
import signal
import subprocess
import sys
import termios
import traceback
import tty
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from types import TracebackType
from typing import IO, Callable, Generator, TextIO

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# The amber the eyes are drawn in, measured off the favicon itself
# (Frontend/public/web-app-manifest-512x512.png) rather than eyeballed. The same
# value the plymouth theme paints its progress bar with, so the boot splash, the
# menu and the installed box's login banner agree.
AMBER_RGB = "f7b718"

# Wide enough for a disk description -- device, model, serial and size -- and
# narrow enough to stay inside 80 columns, which is what a Linux VT on a box with
# no monitor attached at boot tends to be.
MAX_WIDTH = 80

# What `sys.excepthook` is: the three arguments of an exception, and no return.
ExceptHook = Callable[[type[BaseException], BaseException, TracebackType | None], None]

THEME = Theme(
    {
        "loom.brand": "bold yellow",
        "loom.head": "bold",
        "loom.quiet": "dim",
        "loom.ok": "green",
        "loom.warn": "yellow",
        "loom.danger": "bold red",
        "loom.key": "dim",
    }
)


class Aborted(RuntimeError):
    """The operator stopped this.

    One exception for every way of saying no: the wrong word at the interlock, an end
    of file, or Ctrl-C at any prompt below. They are the same event to everything
    downstream -- `loom-install` and `loom-wipe` exit `EXIT_CANCELLED` on it and the
    menu says "cancelled" rather than "failed".

    It lives here rather than in interlock.py, which is where a reader would look for
    it, because `interlock` imports this module: the prompts are what turn a keypress
    into this exception, so the dependency can only run one way.
    """


class Keypress(StrEnum):
    """How a wait for the operator ended."""

    PRESSED = "pressed"
    TIMEOUT = "timeout"
    CLOSED = "closed"
    # Ctrl-C during a countdown. Distinct from PRESSED because the two callers want
    # opposite things from it: stopping an unattended install is the same as any
    # other key, whereas stopping the reboot after an install is the opposite of the
    # enter that brings the reboot forward.
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Ui:
    """The installer's screen.

    One object rather than module-level functions so that a caller can be handed a
    console writing somewhere else -- which is what the tests do.
    """

    out: Console
    err: Console

    @property
    def interactive(self) -> bool:
        """Whether there is somebody at a keyboard on the other end."""
        return self.out.is_terminal

    def clear(self) -> None:
        """Home the cursor and clear the screen.

        Deliberately not the scrollback as well: clearing it is an xterm extension
        and the Linux VT does not implement it.
        """
        if self.interactive:
            self.out.clear()

    def banner(self) -> None:
        """The mark the boot splash just showed, in the two eyes it is made of.

        `ESC ] P nrrggbb` redefines a palette entry on the Linux VT, which is the
        only way to reach an exact colour there: console_codes(4) records that even
        a 24-bit `38;2;r;g;b` is "shoehorned into 16 basic colors", so yellow lands
        on #ffff55 with bold and #aa5500 without -- both far enough from the logo to
        read as a mistake rather than a colour. Index 3 and index 11 are both set
        because bold promotes one to the other.

        Two consequences, both deliberate. It repaints every yellow below, so the
        target-disk line matches the eyes. And it outlives this program -- there is
        no reset, so the rescue shell inherits it too.

        Never anywhere but a VT: console_codes(4) warns that xterm hangs on this
        sequence until somebody presses return, and this program is also run by hand
        from a shell that may be one.

        The colour itself is a *state left on the terminal* rather than anything
        rich renders. `loom-eyes` (branding.nix) prints the art uncoloured and
        writes to this descriptor as a subprocess, precisely so that the caller --
        which is the only thing that knows what console it is on -- decides. So the
        pair is written raw around the call, and selecting index 3 is what makes the
        palette redefinition above visible at all: without it the eyes come out in
        whatever the console's default foreground is.
        """
        if not self.interactive:
            self._draw_eyes()
            return

        if _on_virtual_terminal(self.out.file):
            self.out.file.write(f"\033]P3{AMBER_RGB}\033]PB{AMBER_RGB}")

        # Bold as well as yellow, because bold is what promotes index 3 to index 11
        # -- both redefined above -- and what the appliance's own login banner
        # (box.nix) draws the same pair in.
        self.out.file.write("\033[1;33m")
        self._draw_eyes()
        self.out.file.write("\033[0m")
        self.out.file.flush()

    def _draw_eyes(self) -> None:
        """Run `loom-eyes`, which writes to this descriptor itself.

        The stream is flushed first so that what rich has buffered cannot land
        after the art: the two write to the same descriptor but through different
        buffers. Going through rich instead is not an option -- the art is UTF-8
        half blocks and this console is an ASCII stream (see the module docstring).
        """
        self.out.file.flush()
        try:
            subprocess.run(["loom-eyes"], check=False, timeout=10)
        except (OSError, subprocess.SubprocessError):
            # A stick whose branding failed to build is still a working installer.
            self.out.file.write("  LOOM\n")

    def rule(self) -> None:
        self.out.print("=" * min(self.out.width, MAX_WIDTH), style="loom.quiet")

    def log(self, message: str) -> None:
        self.out.print(Text("[*] ", style="loom.quiet").append(message))

    def note(self, message: str) -> None:
        self.out.print(message, style="loom.quiet")

    def warn(self, message: str) -> None:
        """A problem the operator has to act on, on stderr.

        The palette is keyed on each stream separately, so that `loom-install
        2>install.log` from a terminal writes no escapes into the log.
        """
        self.err.print(Text("[!] ", style="loom.danger").append(message))

    def blank(self) -> None:
        self.out.print()

    def show(self, renderable: RenderableType) -> None:
        """Anything rich can draw: a table, a panel, styled text."""
        self.out.print(renderable)

    def prompt(self, message: str) -> str:
        """Ask for a line, and be forgiving about whitespace around the answer.

        Printed rather than handed to `input()` as its prompt argument, because `input`
        writes to stdout with no styling and no way to route it -- and the prompt has to
        sit inside the palette of whatever was drawn above it.
        """
        self.out.print(message, end="")
        return self._answer().strip()

    def prompt_passphrase(self, message: str) -> str:
        """Ask for a passphrase, and show it while it is typed.

        Echoed, which is not what a passphrase prompt usually does. The threat that
        gives up is an observer at the monitor, and this program concedes that one
        already: it prints the LUKS recovery passphrase to this same screen when it
        finishes, and the console it draws on is a root shell. What it buys is the
        only feedback there is about the keyboard map -- under a wrong one `-`
        arrives as `/` and `y` as `z`, and a masked prompt makes that
        indistinguishable from a passphrase that is simply wrong.

        Not stripped, unlike `prompt`: a passphrase is bytes somebody chose, and
        trimming whitespace out of one would quietly reject a correct answer.
        """
        self.out.print(message, end="")
        return self._answer()

    def _answer(self) -> str:
        """A line from the operator, or however they refused to give one.

        End of file is not a refusal: it is what a console with nothing attached to it
        does, and every caller already treats "" as an answer that is not the one it
        wanted. Ctrl-C is a refusal, and becomes the same exception as typing the wrong
        word at the interlock.
        """
        try:
            return self._read_line()
        except EOFError:
            return ""
        except KeyboardInterrupt:
            # The tty has echoed `^C` and eaten the line, so the cursor is sitting at
            # the end of the prompt with no newline of its own coming. Without this
            # the abort message lands on the same line as the question.
            self.out.file.write("\n")
            self.out.file.flush()
            raise Aborted("Cancelled.") from None

    def _read_line(self) -> str:
        """The blocking read itself, and one of the two places a keypress arrives.

        Separate from the handling above so that it is a seam: a test overrides this
        to be an operator pressing Ctrl-C, and everything that turns that into an
        `Aborted` is still the real thing (tests/test_console.py).
        """
        return input()

    def wait_for_enter(self, message: str) -> None:
        self.prompt(message)

    def countdown(self, message: str, seconds: int, any_key: bool) -> Keypress:
        """Hold the console for a while, and say how that ended.

        Repainted in place with `\\r` so whatever is above -- a recovery passphrase, a
        list of disks about to be destroyed -- stays on screen for the whole countdown.
        Off a terminal there is nothing to repaint into, and one line per second in a
        captured log is worse than no countdown at all, so the deadline is announced
        once instead.

        `any_key` is the difference between the two callers. The reboot after an install
        takes enter, because a stray keypress there costs nothing. The unattended
        install takes any key at all, because a keypress that failed to register is a
        destroyed disk.

        Ctrl-C is `CANCELLED` rather than an exception out of here: `tty.setcbreak`
        leaves ISIG set, so it arrives as a signal and not as the byte the select below
        is waiting for. Caught around the whole block so the terminal is handed back and
        the trailing newline still written.
        """
        announced = False
        outcome = Keypress.TIMEOUT

        try:
            # Whether the console can be drawn on changes what is printed and nothing
            # else. The wait below is the same either way, because a caller that takes
            # any key treats an unreadable stdin as "nobody can stop this" -- which is
            # the last circumstance under which to go ahead and partition a disk.
            with _cbreak(sys.stdin) if any_key else _passthrough():
                for remaining in range(seconds, 0, -1):
                    if self.interactive:
                        # A fixed width, so 9s does not leave behind the stray digit
                        # of the 10s that came before it.
                        self.out.file.write(f"\r  {message} in {remaining:2d}s. ")
                        self.out.file.flush()
                    elif not announced:
                        self.out.print(f"  {message} in {seconds}s.")
                        announced = True

                    outcome = self._wait(1.0, any_key)
                    if outcome is not Keypress.TIMEOUT:
                        break
        except KeyboardInterrupt:
            outcome = Keypress.CANCELLED

        if self.interactive:
            self.out.file.write("\n")
            self.out.file.flush()
        return outcome

    def _wait(self, timeout: float, any_key: bool) -> Keypress:
        """One second of a countdown, and the other place a keypress arrives.

        A method for the same reason `_read_line` is one: it is where this program
        blocks on a keyboard, so it is where a test puts a Ctrl-C without reaching past
        the Ui it was handed.
        """
        return _wait_for_input(timeout, any_key)

    def status_table(self) -> Table:
        """The two-column block the menu's header is made of."""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="loom.key", no_wrap=True, width=12)
        table.add_column(overflow="fold")
        return table

    def panel(
        self, renderable: RenderableType, title: str, style: str = "loom.quiet"
    ) -> Panel:
        """A framed block.

        `box` is left to rich, which substitutes the ASCII drawing for the Unicode one
        off the stream encoding pinned in `build_ui` -- see the module docstring.
        """
        return Panel(
            renderable,
            title=title,
            title_align="left",
            border_style=style,
            padding=(0, 1),
        )


def build_ui() -> Ui:
    """The screen this program was started on.

    `color_system="standard"` is the pin the module docstring argues for: 16 colours,
    which is what a Linux VT has and what the palette sequence in `Ui.banner` redefines
    an entry of. Left to rich it would read the absent `TERM` and settle on 256, and
    every colour would arrive as an approximation of an approximation.
    """
    _pin_stream_encoding()
    return Ui(
        out=Console(
            theme=THEME,
            color_system="standard",
            highlight=False,
            # Off, because almost everything printed here is a string the box
            # supplied -- a disk model, a device path, a line of nixos-install's
            # output -- and rich would read `[...]` in one of them as a style tag
            # and swallow it. Styling is applied with `Text` instead.
            markup=False,
            width=_console_width(sys.stdout),
        ),
        err=Console(
            theme=THEME,
            color_system="standard",
            highlight=False,
            markup=False,
            stderr=True,
            width=_console_width(sys.stderr),
        ),
    )


def _console_width(stream: TextIO) -> int | None:
    """Cap the console, but never widen it.

    None lets rich measure, which is what happens on a wide console; the cap is what
    keeps a disk description on one line on a screen that is wider than anything here
    has to say.
    """
    try:
        return min(os.get_terminal_size(stream.fileno()).columns, MAX_WIDTH)
    except (OSError, ValueError):
        return None


def _pin_stream_encoding() -> None:
    """Put stdout and stderr into ASCII, replacing anything else.

    See the module docstring: this is what selects rich's ASCII renderings and what
    makes a stray byte in a disk model print as `?` rather than abort an install.
    """
    for stream in (sys.stdout, sys.stderr):
        if not isinstance(stream, io.TextIOWrapper):
            continue
        try:
            stream.reconfigure(encoding="ascii", errors="replace")
        except (OSError, ValueError):
            continue


def _on_virtual_terminal(stream: IO[str]) -> bool:
    """Whether this really is /dev/ttyN, rather than a pts or a pipe."""
    try:
        return (
            os.ttyname(stream.fileno()).startswith("/dev/tty")
            and os.ttyname(stream.fileno())[len("/dev/tty") :].isdigit()
        )
    except (OSError, ValueError):
        return False


@contextmanager
def ignoring_interrupts() -> Generator[None]:
    """SIGINT off for a stretch that has to finish once it has started.

    The stretches are the teardowns: letting go of a half-written box, deactivating a
    volume group. A flag would not do, because `KeyboardInterrupt` is raised at whatever
    bytecode boundary the signal happens to land on -- every step would need its own try
    block and the gaps between them would still be open.

    Safe because what it wraps is bounded: everything inside goes through
    `CommandRunner`, whose every call carries `DEFAULT_TIMEOUT_S`. The console cannot be
    made unresponsive for longer than the commands themselves can run.

    The previous handler is restored rather than the default one, so nesting -- or a
    caller that has deliberately ignored SIGINT already -- comes out as it went in.
    """
    previous = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


@contextmanager
def console_restored(ui: Ui) -> Generator[None]:
    """Give the terminal back whatever a child left it in.

    For the menu, around the installer and the wipe. Both are separate processes on the
    menu's own tty, and a child that dies without unwinding -- SIGKILL from systemd, an
    OOM, `subprocess.run` killing it on Ctrl-C -- leaves the terminal however it had it:
    a rich progress display hides the cursor, and a prompt reading a line can leave the
    line discipline anywhere. Nothing else repairs that. `Console.clear()` writes
    `ESC[2J ESC[H` and no more, so redrawing the menu does not.

    Everything here is best effort in the same way `_cbreak` is: off a real terminal
    there is nothing to save and nothing to put back.
    """
    try:
        descriptor = sys.stdin.fileno()
        saved = termios.tcgetattr(descriptor)
    except (OSError, ValueError, termios.error):
        descriptor = -1
        saved = None

    try:
        yield
    finally:
        if saved is not None:
            try:
                termios.tcsetattr(descriptor, termios.TCSADRAIN, saved)
            except (OSError, termios.error):
                pass
        ui.out.show_cursor(True)


def crash_handler(ui: Ui, path: str) -> ExceptHook:
    """What to do with an exception nobody expected: not print it.

    A traceback on an 80-column VT is dozens of lines of scroll over the disk list, the
    warnings and the recovery passphrase. One line stays on screen instead, and the
    traceback goes to a file the rescue shell can read.

    Installed as `sys.excepthook` rather than written as an `except Exception` around
    the body of a `main`, because that is the shape that catches everything -- including
    whatever is raised on the way out of one -- without naming a base class broad enough
    for the linter to object to. It never sees a `KeyboardInterrupt` or a `SystemExit`
    that the caller has already handled.
    """

    def handle(
        kind: type[BaseException],
        error: BaseException,
        tracing: TracebackType | None,
    ) -> None:
        del tracing
        ui.warn(f"Unexpected error: {kind.__name__}: {error}")
        written = write_traceback(path, error)
        if written is not None:
            ui.warn(f"The details are in {written} (menu option 5, the rescue shell).")

    return handle


def write_traceback(path: str, error: BaseException) -> str | None:
    """Put the traceback being handled somewhere it can be read later.

    The last resort behind `sys.excepthook`, and it writes to a file because there is
    nowhere else: installer.nix gives this unit `StandardError = "tty"` rather than the
    journal, so an unhandled exception's only home is the screen -- where it would
    scroll away the disk list and the recovery passphrase that make an 80-column console
    worth reading at all. /run, because the stick is a read-only squashfs.

    Returns the path it wrote, or None when even that failed, which is the caller's cue
    to say nothing about a file that is not there.

    The exception is passed in rather than read from `sys.exc_info()`, because the one
    caller is a `sys.excepthook`, which is handed the exception precisely because it
    runs after the handling of it is over.
    """
    try:
        with open(path, "w", encoding="ascii", errors="replace") as handle:
            traceback.print_exception(error, file=handle)
    except OSError:
        return None
    return path


@contextmanager
def _cbreak(stream: TextIO) -> Generator[None]:
    """Read single keypresses, and give the terminal back however this ends."""
    try:
        descriptor = stream.fileno()
        saved = termios.tcgetattr(descriptor)
    except (OSError, ValueError, termios.error):
        yield
        return

    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, saved)


@contextmanager
def _passthrough() -> Generator[None]:
    yield


def _wait_for_input(timeout: float, any_key: bool) -> Keypress:
    """One second of the countdown, which is also the wait for a keypress.

    A closed stdin is deliberately NOT treated as a keypress. It means nobody can stop
    what comes next, which is the last circumstance under which to go ahead and
    partition a disk -- so the caller sees `CLOSED` and stops.
    """
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):
        return Keypress.CLOSED
    if not ready:
        return Keypress.TIMEOUT

    try:
        data = os.read(sys.stdin.fileno(), 1 if any_key else 4096)
    except OSError:
        return Keypress.CLOSED
    if not data:
        return Keypress.CLOSED
    if any_key or b"\n" in data:
        return Keypress.PRESSED
    return Keypress.TIMEOUT
