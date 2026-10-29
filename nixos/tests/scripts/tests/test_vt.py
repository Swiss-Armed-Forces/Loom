"""Reading a console out of /dev/vcsu.

The arithmetic here decides whether a VM test is asserting the banner, some other row,
or nothing at all -- and getting it wrong is invisible: an off-by-one row still returns
a string, and the assertion that follows fails for a reason that looks like the box's
fault.
"""

import base64

import machines

from loom_tests import vt


def screen(rows: int, columns: int, text: list[str]) -> vt.Screen:
    """A console with `text` laid into it, padded with never-written cells.

    One cell is a codepoint, as the unicode device hands them over: four little-endian
    bytes, and a cell nobody wrote is four zero bytes.
    """
    cells = bytearray(rows * columns * vt.CELL)
    for row, line in enumerate(text):
        for column, character in enumerate(line):
            offset = (row * columns + column) * vt.CELL
            cells[offset : offset + vt.CELL] = ord(character).to_bytes(
                vt.CELL, "little"
            )
    return vt.Screen(rows=rows, columns=columns, cells=bytes(cells))


def booted(text: list[str]) -> machines.FakeMachine:
    """A machine whose console holds `text`, answering both devices it is read from."""
    console = screen(len(text), max(len(line) for line in text), text)
    return machines.FakeMachine(
        {
            "vcsa": (
                base64.b64encode(bytes([console.rows, console.columns, 0, 0])).decode()
            ),
            "vcsu": base64.b64encode(console.cells).decode(),
        }
    )


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


def test_a_character_that_is_not_ascii_reads_as_a_hash():
    """Which is the only way the Loom mark can be matched at all.

    `loom_tests.wifi` looks for a run of '#' rather than for U+2588, because the mark is
    block characters and the tests are strings.
    """
    assert screen(1, 4, ["██▀"]).line(0) == "###."


def test_a_bright_cell_is_still_the_character_that_was_printed():
    """Otherwise a whole login screen reads as the Loom mark.

    The banner is painted bright under a 512-glyph font, and a VGA-style cell cannot say
    whether bit 3 of its attribute is that brightness or the ninth bit of a font index.
    A decoder that assumes the latter answers '#' for every cell of the screen, so the
    mark -- two block groups with a gap -- is nowhere to be found in a screen with no
    gaps in it. The unicode device has no attribute byte to misread.
    """
    assert screen(1, 4, ["LOOM"]).line(0) == "LOOM"


def test_a_cell_nobody_wrote_reads_as_a_dot():
    """'.' and ' ' are different facts: blank screen versus a printed space."""
    assert screen(1, 4, [" x"]).line(0) == " x.."


def test_a_short_buffer_does_not_raise():
    """A console read mid-resize comes back shorter than its own header claims."""
    truncated = vt.Screen(rows=4, columns=80, cells=bytes([65, 0, 0, 0]))
    assert truncated.line(0).startswith("A")
    assert truncated.bottom() == "." * 80


def test_rows_can_be_trimmed_to_the_interesting_columns():
    """The banner assertions only care about the left-hand edge of the screen."""
    assert screen(1, 80, ["  LOOM  starting 12/18"]).line(0, width=8) == "  LOOM  "


def test_only_the_rows_that_exist_come_back():
    assert len(screen(3, 4, []).top(10)) == 3


def test_the_screen_is_read_from_the_tty_it_was_asked_for():
    """Every caller wants tty1, but a test that hardcoded it would hide a typo here.

    Both devices, because the geometry and the contents come from different ones: read
    from two different consoles they would describe two different screens.
    """
    machine = booted(["abcd", "efgh"])

    assert vt.read(machines.as_machine(machine)).line(1) == "efgh"
    assert any("/dev/vcsa1" in call for call in machine.calls), machine.calls
    assert any("/dev/vcsu1" in call for call in machine.calls), machine.calls

    machine.calls.clear()
    vt.read(machines.as_machine(machine), tty="2")
    assert any("/dev/vcsa2" in call for call in machine.calls), machine.calls
    assert any("/dev/vcsu2" in call for call in machine.calls), machine.calls


def test_only_the_header_is_read_from_the_attribute_device():
    """Its cells are the ones that cannot be decoded, so none of them is read."""
    machine = booted(["ab"])

    vt.read(machines.as_machine(machine))

    attributes = [call for call in machine.calls if "vcsa" in call]
    assert attributes == [f"head -c {vt.HEADER} /dev/vcsa1 | base64 -w0"], attributes
