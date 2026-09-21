"""The brand colour, which nothing but an operator's eye would otherwise check.

`loom-eyes` (branding.nix) prints the mark uncoloured and deliberately so: reaching the
exact amber on a Linux VT means redefining a palette entry, and only the caller knows
whether the console in front of it can take that sequence. Which makes the colour
something this program has to leave on the terminal around a subprocess -- and something
that can be dropped without any test failing and without anything looking broken, right
up until somebody sees grey eyes on a box.
"""

import io

from rich.console import Console

from loom_installer.console import AMBER_RGB, Ui

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
