"""What the relay does with what gpm hands it.

The one branch worth pinning here is the distinction `read_events` exists to make: a
short read on a stream socket must not be mistaken for the daemon going away. Getting
that wrong is invisible in a VM test and costs the operator the mouse for a reconnect
interval every time it happens -- on the appliance's only user interface, with no remote
access to notice it from.
"""

import os

from loom_console_mouse.gpm import _EVENT, GPM_DOWN, GPM_UP, GpmClient
from loom_console_mouse.relay import Relay

VC = 1


class _FakeSocket:
    """A canned byte stream, chunked as the test wants, that records being closed."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)
        self.closed = False

    def recv(self, _size: int, /) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""

    def fileno(self) -> int:
        return -1

    def close(self) -> None:
        self.closed = True


def _packed(x: int, y: int, event_type: int) -> bytes:
    return _EVENT.pack(4, 0, 1, 0, 0, x, y, event_type, 1, 0, 0, 0)


def _relay(chunks: list[bytes]):
    """A relay whose console and pty are pipes, so both sides can be read back.

    The pointer ioctls fail on a pipe and are swallowed -- see `pointer.Pointer`.
    """
    console_read, console_write = os.pipe()
    master_read, master_write = os.pipe()
    socket = _FakeSocket(chunks)
    relay = Relay(console_write, GpmClient(socket), master_write, VC)
    return relay, socket, master_read, console_read


def test_a_short_read_does_not_cost_the_mouse() -> None:
    """The held-over bytes are the point: closing here would throw them away."""
    whole = _packed(40, 12, GPM_DOWN)
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
    relay, _socket, master_read, _console = _relay([_packed(3, 4, GPM_UP)])

    relay.handle_gpm()

    os.set_blocking(master_read, False)
    assert os.read(master_read, 4096)
