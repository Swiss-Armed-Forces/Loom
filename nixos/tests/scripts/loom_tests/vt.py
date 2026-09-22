"""What is actually on a virtual console, read out of the kernel's own memory.

Some of what this appliance does can only be asserted by looking at the screen: the login
banner is written straight to the VT by agetty, and tmux's status line is drawn by tmux
into a terminal nothing else can query. `/dev/vcsaN` is that screen -- a four-byte header
of rows, columns and cursor position, then two bytes per cell, character first and
attribute second.

The rendering is one function on purpose, because the two callers want the same three-way
distinction and it is not the obvious one:

    printable ASCII -> the character itself
    anything else   -> '#'
    an empty cell   -> '.'

A block-drawing glyph is stored as its index in the console font, not as a codepoint, so
the Loom mark cannot be read back as text at all -- it comes back as a run of '#', which
is exactly what tests/scripts/loom_tests/wifi.py matches the logo with. A cell that was
never written is 0 and comes back as '.', which is what distinguishes "the screen is
blank here" from "a space was printed here".

This module owns the decoding for every test. Two of them grew their own copy of it while
the scripts were concatenated rather than imported, which is one of the things that
arrangement cost.
"""

import base64
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loom_tests.driver import Machine

HEADER = 4


@dataclass(frozen=True)
class Screen:
    """One console's contents at one moment."""

    rows: int
    columns: int
    # The body after the header: two bytes per cell, row-major.
    cells: bytes

    def line(self, row: int, width: int | None = None) -> str:
        """One row, rendered by the rule in this module's header."""
        columns = self.columns if width is None else min(self.columns, width)
        start = row * self.columns
        return "".join(self._glyph(start + column) for column in range(columns))

    def top(self, count: int, width: int | None = None) -> list[str]:
        """The first `count` rows -- where a banner starts, and where it is cropped."""
        return [self.line(row, width) for row in range(min(count, self.rows))]

    def bottom(self, width: int | None = None) -> str:
        """The last row, which is where tmux draws its status line."""
        return self.line(self.rows - 1, width)

    def _glyph(self, cell: int) -> str:
        offset = cell * 2
        if offset >= len(self.cells):
            return "."
        character = self.cells[offset]
        if 32 <= character < 127:
            return chr(character)
        return "#" if character else "."


def read(machine: "Machine", tty: str = "1") -> Screen:
    """Whatever is on that VT now.

    Through base64 rather than `cat`, because this is binary and the driver's `succeed`
    hands back text: a raw read would mangle every byte that is not valid UTF-8, which
    here is most of the interesting ones.
    """
    raw = base64.b64decode(machine.succeed(f"base64 -w0 /dev/vcsa{tty}"))
    return Screen(rows=raw[0], columns=raw[1], cells=raw[HEADER:])
