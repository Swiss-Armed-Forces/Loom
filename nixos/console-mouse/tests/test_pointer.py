"""The TIOCLINUX argument the kernel actually reads.

`tioclinux()` in drivers/tty/vt/vt.c takes the subcode from the first byte of
the argument and hands `arg + 1` to `set_selection_user()` as a
`struct tiocl_selection`. That one-byte offset leaves the five shorts
misaligned, which is fine -- the kernel copies the struct with
`copy_from_user` -- but it does mean the buffer cannot be built with a plain
aligned struct, and gpm's own `selection_copy()` goes to the same trouble.

An ioctl is not something a unit test can meaningfully perform, so what is
checked here is the byte layout and the sequencing that keeps the kernel's
cached cell honest.
"""

import struct
from typing import NamedTuple

from loom_console_mouse.pointer import (
    _SETSEL,
    TIOCL_SELCLEAR,
    TIOCL_SELPOINTER,
    TIOCL_SETSEL,
    Pointer,
)


class _RecordingPointer(Pointer):
    """A Pointer whose ioctl is a list instead of a syscall."""

    def __init__(self) -> None:
        super().__init__(console_fd=-1)
        self.calls: list[bytes] = []

    def _setsel(self, xs: int, ys: int, xe: int, ye: int, mode: int) -> None:
        self.calls.append(_SETSEL.pack(TIOCL_SETSEL, xs, ys, xe, ye, mode))
        if mode == TIOCL_SELPOINTER:
            self._shown = True
        elif mode == TIOCL_SELCLEAR:
            self._shown = False


class _Selection(NamedTuple):
    """One decoded TIOCL_SETSEL argument, so assertions can name their fields."""

    subcode: int
    xs: int
    ys: int
    xe: int
    ye: int
    mode: int


def _decode(payload: bytes) -> _Selection:
    return _Selection(*struct.unpack("=B5H", payload))


def test_setsel_buffer_is_one_byte_then_five_shorts() -> None:
    """Eleven bytes, not twelve: there is no padding after the subcode."""
    assert _SETSEL.size == 11


def test_showing_the_pointer_sends_a_degenerate_selection() -> None:
    """A pointer is a selection whose start and end are the same cell."""
    pointer = _RecordingPointer()
    pointer.move(40, 12)

    selection = _decode(pointer.calls[-1])
    assert selection.subcode == TIOCL_SETSEL
    assert (selection.xs, selection.ys) == (40, 12)
    assert (selection.xe, selection.ye) == (40, 12)
    assert selection.mode == TIOCL_SELPOINTER


def test_coordinates_are_passed_through_one_based() -> None:
    """The kernel does its own `- 1`.

    `vc_selection()` computes `min_t(u16, v->xs - 1, vc->vc_cols - 1)`, and gpm
    reports 1-based cells, so the two line up with no adjustment. Subtracting
    here as well would put the pointer one cell up and to the left of the
    mouse -- the kind of thing that looks like a calibration problem.
    """
    pointer = _RecordingPointer()
    pointer.move(1, 1)
    selection = _decode(pointer.calls[-1])
    assert (selection.xs, selection.ys) == (1, 1)


def test_hide_clears_rather_than_redrawing() -> None:
    pointer = _RecordingPointer()
    pointer.move(40, 12)
    pointer.hide()

    selection = _decode(pointer.calls[-1])
    assert selection.mode == TIOCL_SELCLEAR


def test_hide_is_a_no_op_when_nothing_is_drawn() -> None:
    """Otherwise every write before the first mouse movement would clear a selection the
    operator might have made on the console by hand."""
    pointer = _RecordingPointer()
    pointer.hide()
    assert not pointer.calls


def test_a_write_is_bracketed_clear_then_show() -> None:
    """The ordering that finding this bug came down to.

    `complement_pos()` caches the cell under the pointer and writes that cache back when
    the pointer next moves. Redrawing *after* the write -- rather than clearing before
    it -- leaves the cache holding the cell as it was beforehand, and the next mouse
    movement paints it over live output.
    """
    pointer = _RecordingPointer()
    pointer.move(40, 12)
    pointer.calls.clear()

    pointer.hide()
    pointer.show()

    modes = [_decode(call).mode for call in pointer.calls]
    assert modes == [TIOCL_SELCLEAR, TIOCL_SELPOINTER]


def test_show_before_any_position_is_known_draws_nothing() -> None:
    pointer = _RecordingPointer()
    pointer.show()
    assert not pointer.calls
