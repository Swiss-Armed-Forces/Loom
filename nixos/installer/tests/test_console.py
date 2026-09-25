"""The brand colour, and what a prompt does when nobody answers it.

`loom-eyes` (branding.nix) prints the mark uncoloured and deliberately so: reaching the
exact amber on a Linux VT means redefining a palette entry, and only the caller knows
whether the console in front of it can take that sequence. Which makes the colour
something this program has to leave on the terminal around a subprocess -- and something
that can be dropped without any test failing and without anything looking broken, right
up until somebody sees grey eyes on a box.

The prompts are here for the opposite reason: Ctrl-C is the one answer an operator can
give to every question this program asks, and until it was handled it was also the one
that put a Python traceback on a console whose whole job is being readable.
"""

import io
from dataclasses import dataclass

import pytest
from rich.console import Console

from loom_installer.console import AMBER_RGB, Aborted, Keypress, Ui

# ESC[1m + ESC[33m: bold as well as yellow, because bold is what promotes palette
# index 3 to index 11, and the appliance's own login banner draws the same pair in
# both.
BOLD_YELLOW = "\033[1;33m"
RESET = "\033[0m"


def _ui_over(buffer: io.StringIO, terminal: bool) -> Ui:
    console = Console(
        file=buffer,
        force_terminal=terminal,
        color_system="standard",
        markup=False,
        highlight=False,
        width=80,
    )
    return Ui(out=console, err=console)


def test_the_eyes_are_drawn_in_the_brand_colour() -> None:
    # The regression this file exists for: without the pair, the palette entry
    # redefined for a VT is never selected, so redefining it changes nothing and the
    # mark comes out in whatever the console's default foreground is.
    buffer = io.StringIO()
    _ui_over(buffer, terminal=True).banner()

    written = buffer.getvalue()
    assert BOLD_YELLOW in written, written
    assert RESET in written, written
    assert written.index(BOLD_YELLOW) < written.index(RESET), written


def test_off_a_terminal_the_mark_carries_no_escapes() -> None:
    # `loom-install 2>install.log`, or the unit's output in the journal: escapes in
    # either is what the whole console module is arranged to avoid.
    buffer = io.StringIO()
    _ui_over(buffer, terminal=False).banner()

    assert "\033" not in buffer.getvalue(), buffer.getvalue()


def test_the_palette_sequence_is_kept_off_anything_but_a_virtual_terminal() -> None:
    # console_codes(4): an xterm hangs on `ESC ] P nrrggbb` until somebody presses
    # return, and this program is also run by hand from a shell that may be one. A
    # StringIO has no terminal name at all, which is the safe side of that test.
    buffer = io.StringIO()
    _ui_over(buffer, terminal=True).banner()

    assert AMBER_RGB not in buffer.getvalue(), buffer.getvalue()


@dataclass(frozen=True)
class InterruptedUi(Ui):
    """A console where the operator presses Ctrl-C instead of answering.

    Overriding the two methods that block on a keyboard, so everything around them --
    the prompt, the newline, the exception, the countdown's own bookkeeping -- is the
    real thing.
    """

    def _read_line(self) -> str:
        raise KeyboardInterrupt

    def _wait(self, timeout: float, any_key: bool) -> Keypress:
        del timeout, any_key
        raise KeyboardInterrupt


def _interrupted_ui(buffer: io.StringIO) -> InterruptedUi:
    console = _ui_over(buffer, terminal=True).out
    return InterruptedUi(out=console, err=console)


def test_ctrl_c_at_a_prompt_is_the_same_answer_as_refusing_the_interlock() -> None:
    # One exception for every way of saying no, which is what lets `loom-install` and
    # `loom-wipe` exit "cancelled" rather than "failed" without knowing which it was.
    with pytest.raises(Aborted):
        _interrupted_ui(io.StringIO()).prompt("  Type INSTALL to proceed: ")


def test_a_cancelled_passphrase_prompt_is_the_same_answer() -> None:
    # The prompt on a --lock-key stick, which is reached before anything is written
    # precisely so that changing your mind there costs nothing.
    with pytest.raises(Aborted):
        _interrupted_ui(io.StringIO()).prompt_passphrase("  Key stick passphrase: ")


def test_a_cancelled_prompt_leaves_the_cursor_on_its_own_line() -> None:
    # The tty has echoed `^C` and eaten the line, so without this the message about
    # having cancelled lands on the same line as the question that was asked.
    buffer = io.StringIO()

    with pytest.raises(Aborted):
        _interrupted_ui(buffer).prompt("  Choice [5]: ")

    assert buffer.getvalue().endswith("\n"), buffer.getvalue()


def test_ctrl_c_during_a_countdown_is_a_keypress_rather_than_an_exception() -> None:
    # `tty.setcbreak` leaves ISIG set, so Ctrl-C arrives as a signal and not as the
    # byte the countdown is waiting for. Raising out of here would take the menu down
    # with it -- and systemd would restart it two seconds later, counting down again
    # onto the same disk.
    outcome = _interrupted_ui(io.StringIO()).countdown("Starting", 60, any_key=True)

    assert outcome is Keypress.CANCELLED
