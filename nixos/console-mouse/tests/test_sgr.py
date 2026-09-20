"""What one gpm event becomes.

This is the half of the shim that can be tested without a console, a mouse or
a pty, and it is also the half where the bookkeeping is subtle: gpm reports a
press as the whole new button mask, a release as only the button released, and
a wheel notch as a move with no button at all. Each of those is pinned here.
"""

from loom_console_mouse.gpm import (
    GPM_B_LEFT,
    GPM_B_MIDDLE,
    GPM_B_RIGHT,
    GPM_DOWN,
    GPM_DRAG,
    GPM_MOVE,
    GPM_SINGLE,
    GPM_UP,
    GpmEvent,
)
from loom_console_mouse.sgr import PointerState, translate


def event(
    *,
    type: int,
    x: int = 10,
    y: int = 5,
    buttons: int = 0,
    wdy: int = 0,
    modifiers: int = 0,
) -> GpmEvent:
    return GpmEvent(
        buttons=buttons,
        modifiers=modifiers,
        vc=1,
        dx=0,
        dy=0,
        x=x,
        y=y,
        type=type,
        clicks=0,
        margin=0,
        wdx=0,
        wdy=wdy,
    )


def test_left_press_reports_button_zero() -> None:
    result = translate(event(type=GPM_DOWN, buttons=GPM_B_LEFT), PointerState.initial())
    assert result.report == b"\033[<0;10;5M"
    assert result.state.buttons == GPM_B_LEFT


def test_press_reports_the_new_button_not_the_whole_mask() -> None:
    """gpm sends the full current mask on a press.

    `processmouse.c` sets `event->buttons` to the new state and only decides
    DOWN-vs-UP by comparing it with the old one, so pressing right while left
    is already held arrives as `LEFT|RIGHT`. Reporting that naively would emit
    button 0 -- another left press -- instead of the right button that was
    actually pressed.
    """
    held = PointerState(x=10, y=5, buttons=GPM_B_LEFT)
    result = translate(event(type=GPM_DOWN, buttons=GPM_B_LEFT | GPM_B_RIGHT), held)
    assert result.report == b"\033[<2;10;5M"


def test_release_reports_the_released_button() -> None:
    """For an up event gpm has already XORed the field down to one button."""
    held = PointerState(x=10, y=5, buttons=GPM_B_MIDDLE)
    result = translate(event(type=GPM_UP, buttons=GPM_B_MIDDLE), held)
    assert result.report == b"\033[<1;10;5m"
    assert result.state.buttons == 0


def test_click_flags_do_not_confuse_the_type() -> None:
    """GPM_SINGLE and friends ride in the same field as the event type."""
    result = translate(
        event(type=GPM_DOWN | GPM_SINGLE, buttons=GPM_B_LEFT),
        PointerState.initial(),
    )
    assert result.report == b"\033[<0;10;5M"


def test_wheel_is_read_from_wdy_not_from_a_button() -> None:
    """The imps2 protocol reports a notch as a move with wdy set.

    `M_imps2` in gpm's src/mice.c sets wdy and leaves buttons at zero; the
    GPM_B_UP/GPM_B_DOWN bits are only ever set by the ms3 protocol. A wheel
    keyed off those bits would never fire on this appliance.
    """
    up = translate(event(type=GPM_MOVE, wdy=1), PointerState.initial())
    down = translate(event(type=GPM_MOVE, wdy=-1), PointerState.initial())
    assert up.report == b"\033[<64;10;5M"
    assert down.report == b"\033[<65;10;5M"


def test_wheel_does_not_disturb_the_held_buttons() -> None:
    held = PointerState(x=10, y=5, buttons=GPM_B_LEFT)
    result = translate(event(type=GPM_MOVE, wdy=-1), held)
    assert result.state.buttons == GPM_B_LEFT


def test_drag_sets_the_motion_bit_over_the_held_button() -> None:
    held = PointerState(x=1, y=1, buttons=GPM_B_LEFT)
    result = translate(event(type=GPM_DRAG, buttons=GPM_B_LEFT), held)
    assert result.report == b"\033[<32;10;5M"
    assert result.moved is True


def test_plain_motion_uses_button_three_plus_motion() -> None:
    result = translate(event(type=GPM_MOVE), PointerState.initial())
    assert result.report == b"\033[<35;10;5M"


def test_motion_that_does_not_move_reports_nothing() -> None:
    """gpm replays the current position to a client the moment it registers.

    That synthetic event must not become input: it would land in whatever pane
    is focused before the operator has touched anything.
    """
    parked = PointerState(x=10, y=5, buttons=0)
    result = translate(event(type=GPM_MOVE), parked)
    assert result.report == b""
    assert result.moved is False


def test_drag_that_does_not_move_reports_nothing() -> None:
    held = PointerState(x=10, y=5, buttons=GPM_B_LEFT)
    result = translate(event(type=GPM_DRAG, buttons=GPM_B_LEFT), held)
    assert result.report == b""


def test_modifiers_are_folded_into_the_button_field() -> None:
    """Shift is bit 0 of the console shift state and bit 2 (value 4) in SGR."""
    result = translate(
        event(type=GPM_DOWN, buttons=GPM_B_LEFT, modifiers=1 << 0),
        PointerState.initial(),
    )
    assert result.report == b"\033[<4;10;5M"


def test_alt_and_altgr_both_mean_meta_and_do_not_double() -> None:
    both = translate(
        event(type=GPM_DOWN, buttons=GPM_B_LEFT, modifiers=(1 << 1) | (1 << 3)),
        PointerState.initial(),
    )
    assert both.report == b"\033[<8;10;5M"


def test_coordinates_are_passed_through_unclamped() -> None:
    """The whole reason for SGR rather than the legacy encoding.

    The kernel's own report puts each coordinate in one byte as `'!' + value`,
    which stops at 223 -- against a console branding.nix measures at 426x123.
    """
    result = translate(
        event(type=GPM_DOWN, x=400, y=119, buttons=GPM_B_LEFT),
        PointerState.initial(),
    )
    assert result.report == b"\033[<0;400;119M"
