"""The doubles this suite shares, in one place.

`test_gpm.py` and `test_relay.py` each carried their own socket double and their own
event packer, and they had already drifted: one recorded `close()`, the other did not;
one hardcoded `GPM_DOWN`, the other parameterised the type. Two doubles for one
protocol, differing in exactly the dimension the other file needed, is how a test starts
passing for the wrong reason.

Named `doubles_console_mouse` rather than `doubles`: `appliance-pytest` runs every
appliance suite in one pytest session with no packages, so two modules called
`doubles.py` would collide. The sibling suites are named the same way --
`ready/tests/doubles.py` aside, `portal/tests/doubles_portal.py`,
`installer/tests/fakes.py`, `tests/scripts/tests/machines.py`.
"""

from loom_console_mouse.gpm import _EVENT, GPM_DOWN


class FakeSocket:
    """A canned byte stream, chunked as the test wants, that records being closed."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)
        self.closed = False

    def recv(self, _size: int, /) -> bytes:
        # The size is ignored on purpose: the chunking is the test's, which is what
        # lets one exercise a record split across two reads.
        return self._chunks.pop(0) if self._chunks else b""

    def fileno(self) -> int:
        return -1

    def close(self) -> None:
        self.closed = True


def packed(
    x: int, y: int, event_type: int = GPM_DOWN, buttons: int = 4, wdy: int = 0
) -> bytes:
    """One `Gpm_Event` on the wire.

    `wdy` is a parameter because a wheel notch is not a type of its own -- it is a move
    carrying a wheel delta, which is the distinction `relay._handle_event` has to make.
    """
    return _EVENT.pack(buttons, 0, 1, 0, 0, x, y, event_type, 1, 0, 0, wdy)
