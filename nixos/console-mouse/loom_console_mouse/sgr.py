"""Turning gpm events into SGR (1006) mouse reports.

SGR rather than the original X10 encoding, and that is not a style preference.
The legacy form puts each coordinate in one byte as `value + 040`, which caps
at 223 addressable cells -- against a console that `branding.nix` measures at
426x123 on the panel this appliance was tested on, and more than that on a 4K
panel. It also has no room for a wheel. SGR is decimal text and has neither
limit. tmux parses both (`tty-keys.c`) and asks for SGR unconditionally when
`mouse` is on, so there is nothing to negotiate.

Everything here is pure: events in, bytes out, no I/O and no globals. That is
what makes it the part worth unit-testing, and the tests are where the button
bookkeeping below is actually pinned down.
"""

from typing import NamedTuple

from loom_console_mouse.gpm import (
    GPM_B_LEFT,
    GPM_B_MIDDLE,
    GPM_B_RIGHT,
    GPM_DOWN,
    GPM_DRAG,
    GPM_MOVE,
    GPM_UP,
    GpmEvent,
)

# SGR button numbers. Wheel notches are buttons 64 and 65; a report with bit 5
# set (32) is a motion report for the button in the low bits.
_SGR_LEFT = 0
_SGR_MIDDLE = 1
_SGR_RIGHT = 2
_SGR_NONE = 3
_SGR_MOTION = 32
_SGR_WHEEL_UP = 64
_SGR_WHEEL_DOWN = 65

# gpm's button bits are not in the order anyone would guess -- right is the low
# bit -- so this table is the one place the two orderings meet. Ordered
# left-middle-right so that a chord resolves to the same button every time
# rather than to whichever bit happened to be tested first.
_BUTTON_ORDER: tuple[tuple[int, int], ...] = (
    (GPM_B_LEFT, _SGR_LEFT),
    (GPM_B_MIDDLE, _SGR_MIDDLE),
    (GPM_B_RIGHT, _SGR_RIGHT),
)

# Shift state, as the console keyboard driver reports it (linux/keyboard.h:
# KG_SHIFT 0, KG_ALTGR 1, KG_CTRL 2, KG_ALT 3) mapped onto the bits xterm
# defines for a mouse report. AltGr is folded onto meta with Alt, which is what
# a console keymap means by it.
_MODIFIER_BITS: tuple[tuple[int, int], ...] = (
    (1 << 0, 4),  # shift
    (1 << 3, 8),  # alt   -> meta
    (1 << 1, 8),  # altgr -> meta
    (1 << 2, 16),  # ctrl
)


class PointerState(NamedTuple):
    """Where the pointer is and what is held down.

    Carried between events because gpm does not say everything needed on its
    own: a GPM_DOWN reports the *whole* current button mask rather than the
    button that just went down (`src/daemon/processmouse.c:211-214`), so the
    newly-pressed button is only recoverable by diffing against the previous
    mask.
    """

    x: int
    y: int
    buttons: int

    @classmethod
    def initial(cls) -> "PointerState":
        # (0, 0) rather than (1, 1), which is a real cell: gpm hands a client
        # the current pointer position the moment it registers, and starting
        # off-grid makes that first event count as a move so the pointer gets
        # drawn straight away -- including in the corner case where it really
        # is parked at the top left.
        return cls(x=0, y=0, buttons=0)


class Translation(NamedTuple):
    """What one gpm event becomes.

    `report` is empty whenever the event should produce no input -- gpm sends
    a GPM_MOVE on connect, for instance, so that a client knows where the
    pointer already is, and that one is a position update and nothing more.
    """

    report: bytes
    state: PointerState
    moved: bool


def _modifiers(event: GpmEvent) -> int:
    # An OR rather than a sum, which is why Alt and AltGr can both map onto
    # bit 8 without doubling it.
    total = 0
    for console_bit, sgr_bit in _MODIFIER_BITS:
        if event.modifiers & console_bit:
            total |= sgr_bit
    return total


def _sgr_button(mask: int) -> int:
    for gpm_bit, sgr in _BUTTON_ORDER:
        if mask & gpm_bit:
            return sgr
    return _SGR_NONE


def encode(button: int, x: int, y: int, *, pressed: bool) -> bytes:
    """One SGR report. `x` and `y` are 1-based, as tmux and xterm expect."""
    final = "M" if pressed else "m"
    return f"\033[<{button};{x};{y}{final}".encode("ascii")


def translate(event: GpmEvent, previous: PointerState) -> Translation:
    """Turn one gpm event into at most one SGR report."""
    x, y = event.x, event.y
    moved = (x, y) != (previous.x, previous.y)
    modifiers = _modifiers(event)

    # The wheel first, and by `wdy` rather than by a button bit. For the
    # `imps2` protocol console-mouse.nix selects, a notch arrives as an event
    # with no button set and a non-zero wdy (src/mice.c, `M_imps2`); the
    # GPM_B_UP/GPM_B_DOWN bits are only ever set by the `ms3` protocol. Checked
    # before the type switch because the carrying event is an ordinary
    # GPM_MOVE.
    if event.wdy:
        button = _SGR_WHEEL_UP if event.wdy > 0 else _SGR_WHEEL_DOWN
        return Translation(
            report=encode(button | modifiers, x, y, pressed=True),
            state=PointerState(x=x, y=y, buttons=previous.buttons),
            moved=moved,
        )

    bare = event.bare_type

    if bare == GPM_DOWN:
        # `buttons` is the whole new mask, so the button that actually went
        # down is what the previous mask did not have.
        pressed_now = event.buttons & ~previous.buttons
        button = _sgr_button(pressed_now if pressed_now else event.buttons)
        return Translation(
            report=encode(button | modifiers, x, y, pressed=True),
            state=PointerState(x=x, y=y, buttons=event.buttons),
            moved=moved,
        )

    if bare == GPM_UP:
        # For an up event gpm has already XORed the field down to the button
        # that was released (`event->buttons^=oldB`, processmouse.c:228), so
        # this one can be taken at face value.
        button = _sgr_button(event.buttons)
        return Translation(
            report=encode(button | modifiers, x, y, pressed=False),
            state=PointerState(x=x, y=y, buttons=previous.buttons & ~event.buttons),
            moved=moved,
        )

    if bare == GPM_DRAG:
        if not moved:
            return Translation(
                report=b"",
                state=PointerState(x=x, y=y, buttons=event.buttons),
                moved=False,
            )
        button = _sgr_button(event.buttons) | _SGR_MOTION
        return Translation(
            report=encode(button | modifiers, x, y, pressed=True),
            state=PointerState(x=x, y=y, buttons=event.buttons),
            moved=True,
        )

    if bare == GPM_MOVE:
        if not moved:
            # gpm hands a client its current position the moment it registers
            # (`processconn.c`, "if the client gets motions, give it the
            # current position"). That synthetic event must not turn into
            # input -- it would land in whatever pane is focused before the
            # operator has touched anything.
            return Translation(
                report=b"",
                state=PointerState(x=x, y=y, buttons=previous.buttons),
                moved=False,
            )
        button = _SGR_NONE | _SGR_MOTION
        return Translation(
            report=encode(button | modifiers, x, y, pressed=True),
            state=PointerState(x=x, y=y, buttons=previous.buttons),
            moved=True,
        )

    return Translation(
        report=b"",
        state=PointerState(x=x, y=y, buttons=previous.buttons),
        moved=moved,
    )
