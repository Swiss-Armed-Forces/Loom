"""The wire format, which is a C struct and therefore a thing to get exactly right.

There is no version negotiation on /dev/gpmctl and no framing: a client writes one
`Gpm_Connect` and then reads fixed-size `Gpm_Event` records forever. A struct format
string that is one byte out does not fail, it silently yields nonsense coordinates -- so
the sizes are asserted rather than trusted.
"""

import struct

from loom_console_mouse.gpm import (
    _CONNECT,
    _EVENT,
    GPM_BARE_EVENTS,
    GPM_DOWN,
    GPM_MFLAG,
    GPM_SINGLE,
    GpmClient,
    GpmEvent,
    connect_payload,
)


def test_connect_struct_is_sixteen_bytes() -> None:
    """Unsigned short x4, then int x2, all naturally aligned."""
    assert _CONNECT.size == 16


def test_event_struct_is_twenty_eight_bytes() -> None:
    """2 chars, a short, 4 shorts, 3 ints (two of them enums), 2 shorts.

    The comment in gpm.h -- "try to be a multiple of 4" -- is the author telling us this
    layout is deliberate and unpadded.
    """
    assert _EVENT.size == 28


def test_event_fields_land_where_the_c_struct_puts_them() -> None:
    packed = _EVENT.pack(
        4,  # buttons  (GPM_B_LEFT)
        1,  # modifiers
        7,  # vc
        -1,  # dx
        2,  # dy
        40,  # x
        12,  # y
        GPM_DOWN,  # type
        1,  # clicks
        0,  # margin
        0,  # wdx
        -1,  # wdy
    )
    event = GpmEvent(*_EVENT.unpack(packed))
    assert event.buttons == 4
    assert event.vc == 7
    assert event.x == 40
    assert event.y == 12
    assert event.wdy == -1


def test_bare_type_masks_off_the_click_flags() -> None:
    event = GpmEvent(
        buttons=4,
        modifiers=0,
        vc=1,
        dx=0,
        dy=0,
        x=1,
        y=1,
        type=GPM_DOWN | GPM_SINGLE | GPM_MFLAG,
        clicks=0,
        margin=0,
        wdx=0,
        wdy=0,
    )
    assert event.type != GPM_DOWN
    assert event.bare_type == GPM_DOWN
    assert event.bare_type == event.type & GPM_BARE_EVENTS


class _FakeSocket:
    """Hands back a canned byte stream in whatever chunks the test asks for."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    def recv(self, _size: int, /) -> bytes:
        # The size is ignored on purpose: the chunking is the test's, which is what
        # lets one exercise a record split across two reads.
        return self._chunks.pop(0) if self._chunks else b""

    def fileno(self) -> int:
        return -1

    def close(self) -> None:
        pass


def _packed(x: int, y: int) -> bytes:
    return _EVENT.pack(4, 0, 1, 0, 0, x, y, GPM_DOWN, 1, 0, 0, 0)


def test_a_split_record_is_held_over_to_the_next_read() -> None:
    """This is a SOCK_STREAM, so a short read is a fact of life, not a bug.

    Dropping the tail of a partial struct would resynchronise the stream one byte at a
    time and turn every subsequent event into garbage.
    """
    whole = _packed(40, 12)
    client = GpmClient(_FakeSocket([whole[:10], whole[10:]]))

    # An empty list, never None: the caller drops the connection on a close, and
    # doing that here would throw the ten held-over bytes away.
    assert client.read_events() == []
    events = client.read_events()
    assert events is not None
    assert len(events) == 1
    assert (events[0].x, events[0].y) == (40, 12)


def test_a_closed_connection_is_distinguishable_from_a_short_read() -> None:
    """The distinction the caller acts on: only one of them means "no mouse"."""
    client = GpmClient(_FakeSocket([]))

    assert client.read_events() is None


def test_several_records_in_one_read_all_come_back() -> None:
    client = GpmClient(_FakeSocket([_packed(1, 2) + _packed(3, 4)]))
    events = client.read_events()
    assert events is not None
    assert [(e.x, e.y) for e in events] == [(1, 2), (3, 4)]


def test_connect_payload_carries_the_masks_and_the_console() -> None:
    """Field order matters and is not obvious: both masks come before the pid.

    Getting it wrong would register for console 0 with a pid-shaped event mask
    -- which gpm accepts without complaint and then never sends anything for.
    """
    payload = connect_payload(vc=1, event_mask=0b1111, default_mask=0b0001, pid=4242)

    event_mask, default_mask, min_mod, max_mod, pid, vc = struct.unpack(
        "=HHHHii", payload
    )
    assert (event_mask, default_mask) == (0b1111, 0b0001)
    # Any modifier is acceptable: the console shift state is not a filter here,
    # it is forwarded on to the pane.
    assert (min_mod, max_mod) == (0, 0xFFFF)
    assert (pid, vc) == (4242, 1)
