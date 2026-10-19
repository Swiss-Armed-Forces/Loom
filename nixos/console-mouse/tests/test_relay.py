"""What the relay does with what gpm hands it.

The one branch worth pinning here is the distinction `read_events` exists to make: a
short read on a stream socket must not be mistaken for the daemon going away. Getting
that wrong is invisible in a VM test and costs the operator the mouse for a reconnect
interval every time it happens -- on the appliance's only user interface, with no remote
access to notice it from.
"""

import os
import time

from doubles_console_mouse import FakeSocket, packed

from loom_console_mouse.gpm import GPM_DOWN, GPM_MOVE, GPM_UP, GpmClient
from loom_console_mouse.relay import Relay

VC = 1


def _relay(chunks: list[bytes]):
    """A relay whose console and pty are pipes, so both sides can be read back.

    The pointer ioctls fail on a pipe and are swallowed -- see `pointer.Pointer`.
    """
    console_read, console_write = os.pipe()
    master_read, master_write = os.pipe()
    socket = FakeSocket(chunks)
    relay = Relay(console_write, GpmClient(socket), master_write, VC)
    return relay, socket, master_read, console_read


def test_a_short_read_does_not_cost_the_mouse() -> None:
    """The held-over bytes are the point: closing here would throw them away."""
    whole = packed(40, 12, GPM_DOWN)
    relay, socket, master_read, _console = _relay([whole[:10], whole[10:]])

    relay.handle_gpm()

    assert not socket.closed

    relay.handle_gpm()

    os.set_blocking(master_read, False)
    assert os.read(master_read, 4096).startswith(b"\033[<")


def test_the_daemon_going_away_drops_the_connection() -> None:
    """The other half of the same distinction, and what the reconnect hangs off."""
    relay, socket, _master, _console = _relay([])

    relay.handle_gpm()

    assert socket.closed


def test_a_whole_record_is_reported_straight_away() -> None:
    """A press is not coalesced: only pure motion is."""
    relay, _socket, master_read, _console = _relay([packed(3, 4, GPM_UP)])

    relay.handle_gpm()

    os.set_blocking(master_read, False)
    assert os.read(master_read, 4096)


def test_a_wheel_notch_is_not_coalesced_as_motion() -> None:
    """A notch is a GPM_MOVE carrying `wdy`, which the type table alone cannot see.

    Classified as pure motion it would be held in `_motion.pending`, where the next
    notch inside the same 16ms frame overwrites it -- so sustained scrolling arrives at
    one notch per frame, and a pointer drift between two notches eats one outright.
    """
    notches = packed(5, 5, GPM_MOVE, buttons=0, wdy=1) * 3
    relay, _socket, master_read, _console = _relay([notches])

    relay.handle_gpm()

    os.set_blocking(master_read, False)
    written = os.read(master_read, 4096)
    assert written.count(b"\033[<") == 3, written


def test_pure_motion_is_still_coalesced() -> None:
    """The other half: drift with no button down is exactly what may be dropped."""
    moves = packed(5, 5, GPM_MOVE, buttons=0) + packed(6, 6, GPM_MOVE, buttons=0)
    relay, _socket, master_read, _console = _relay([moves])

    relay.handle_gpm()

    os.set_blocking(master_read, False)
    try:
        written = os.read(master_read, 4096)
    except BlockingIOError:
        written = b""
    assert written == b""

    # pylint: disable-next=protected-access
    relay._flush_motion(time.monotonic() + 1.0)
    assert os.read(master_read, 4096).count(b"\033[<") == 1
