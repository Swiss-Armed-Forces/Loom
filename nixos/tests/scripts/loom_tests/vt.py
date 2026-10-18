"""What is actually on a virtual console, read out of the kernel's own memory.

Some of what this appliance does can only be asserted by looking at the screen: the login
banner is written straight to the VT by agetty, and tmux's status line is drawn by tmux
into a terminal nothing else can query. Two devices answer that question and this module
reads both: `/dev/vcsaN` for its four-byte header of rows, columns and cursor position,
and `/dev/vcsuN` for the contents -- one four-byte codepoint per cell, row-major.

The contents come from the unicode device rather than from the cells behind that header,
and that is the whole of what makes this reliable. `/dev/vcsa` hands back a VGA-style
cell: a *font index* and an attribute byte, neither of which is the character. The index
is only a character while the font maps it to one, the attribute's bit 3 is the ninth bit
of that index under some fonts and the intensity under others, and the appliance paints
its banner bright under a 512-glyph Cozette -- so the two readings disagree on every cell
of the login screen, and the one that says "block glyph everywhere" is the wrong one.
`/dev/vcsu` is the codepoint the kernel recorded when the cell was written, whatever font
was loaded then or now.

The rendering is one function on purpose, because the two callers want the same three-way
distinction and it is not the obvious one:

    printable ASCII -> the character itself
    anything else   -> '#'
    an empty cell   -> '.'

The Loom mark is drawn in block characters, so it comes back as a run of '#', which is
exactly what tests/scripts/loom_tests/wifi.py matches the logo with. A cell that was never
written is 0 and comes back as '.', which is what distinguishes "the screen is blank here"
from "a space was printed here".

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

# One cell of /dev/vcsu: a codepoint as a little-endian 32-bit word.
CELL = 4


@dataclass(frozen=True)
class Screen:
    """One console's contents at one moment."""

    rows: int
    columns: int
    # The unicode screen: four bytes per cell, row-major, no header of its own.
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
        offset = cell * CELL
        if offset + CELL > len(self.cells):
            return "."
        codepoint = int.from_bytes(self.cells[offset : offset + CELL], "little")
        if 32 <= codepoint < 127:
            return chr(codepoint)
        return "#" if codepoint else "."


def read(machine: "Machine", tty: str = "1") -> Screen:
    """Whatever is on that VT now.

    Through base64 rather than `cat`, because this is binary and the driver's `succeed`
    hands back text: a raw read would mangle every byte that is not valid UTF-8, which
    here is most of the interesting ones.

    Two reads rather than one, and separate calls rather than one `succeed` with two
    commands: `base64 -w0` writes no trailing newline, so two outputs handed back
    together would be one string with no boundary in it.
    """
    header = base64.b64decode(
        machine.succeed(f"head -c {HEADER} /dev/vcsa{tty} | base64 -w0")
    )
    cells = base64.b64decode(machine.succeed(f"base64 -w0 /dev/vcsu{tty}"))
    return Screen(rows=header[0], columns=header[1], cells=cells)
