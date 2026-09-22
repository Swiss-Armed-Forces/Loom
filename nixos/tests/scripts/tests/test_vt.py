"""Reading a console out of /dev/vcsa.

The arithmetic here decides whether a VM test is asserting the banner, some other row,
or nothing at all -- and getting it wrong is invisible: an off-by-one row still returns
a string, and the assertion that follows fails for a reason that looks like the box's
fault. Before this was a module it could only be exercised by booting a machine for ten
minutes.
"""

import base64

import machines

from loom_tests import vt


def screen(rows: int, columns: int, text: list[str]) -> vt.Screen:
    """A console with `text` laid into it, padded with never-written cells."""
    cells = bytearray(rows * columns * 2)
    for row, line in enumerate(text):
        for column, character in enumerate(line):
            cells[(row * columns + column) * 2] = ord(character)
    return vt.Screen(rows=rows, columns=columns, cells=bytes(cells))


def test_a_row_comes_back_as_the_text_that_was_printed():
    assert screen(3, 8, ["  LOOM  "]).line(0) == "  LOOM  "


def test_the_status_line_is_the_last_row_whatever_the_height():
    """Tmux draws it at the bottom, and the bottom moves with the console font.

    The three heights are the grids nixos/branding.nix's font table produces on a real
    panel, which is the range this has to be right across.
    """
    for rows in (25, 61, 123):
        console = screen(rows, 10, [""] * (rows - 1) + ["starting"])
        assert console.bottom().startswith("starting"), rows


def test_a_glyph_that_is_not_ascii_reads_as_a_hash():
    """Which is the only way the Loom mark can be matched at all.

    A block-drawing character is stored as its index in the console font, not as a
    codepoint, so `loom_tests.wifi` looks for a run of '#' rather than for U+2588.
    """
    console = vt.Screen(
        rows=1, columns=4, cells=bytes([0xDB, 0, 0xDB, 0, 0xDF, 0, 0, 0])
    )
    assert console.line(0) == "###."


def test_a_cell_nobody_wrote_reads_as_a_dot():
    """'.' and ' ' are different facts: blank screen versus a printed space."""
    assert screen(1, 4, [" x"]).line(0) == " x.."


def test_a_short_buffer_does_not_raise():
    """A console read mid-resize comes back shorter than its own header claims."""
    truncated = vt.Screen(rows=4, columns=80, cells=bytes([65, 0]))
    assert truncated.line(0).startswith("A")
    assert truncated.bottom() == "." * 80


def test_rows_can_be_trimmed_to_the_interesting_columns():
    """The banner assertions only care about the left-hand edge of the screen."""
    assert screen(1, 80, ["  LOOM  starting 12/18"]).line(0, width=8) == "  LOOM  "


def test_only_the_rows_that_exist_come_back():
    assert len(screen(3, 4, []).top(10)) == 3


def test_the_screen_is_read_from_the_tty_it_was_asked_for():
    """Every caller wants tty1, but a test that hardcoded it would hide a typo here."""
    console = screen(2, 4, ["abcd", "efgh"])
    raw = bytes([console.rows, console.columns, 0, 0]) + console.cells
    machine = machines.FakeMachine({"vcsa": base64.b64encode(raw).decode()})

    assert vt.read(machine).line(1) == "efgh"
    assert "/dev/vcsa1" in machine.calls[0]
    vt.read(machine, tty="2")
    assert "/dev/vcsa2" in machine.calls[1]
