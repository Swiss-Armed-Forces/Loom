"""The gpm client protocol, spoken directly rather than through libgpm.

Two structs and a unix socket, and that really is the whole of it: connect to
/dev/gpmctl, write one `Gpm_Connect`, then read a stream of `Gpm_Event`. The
`GPM_USE_MAGIC` framing that `src/lib/liblow.c` can be built with is `#undef`ed in
`src/headers/gpmInt.h`, so there is no per-message prefix to skip.

Spoken directly rather than by parsing `mev`'s output, because `mev` prints `type`,
position, delta, buttons and modifiers -- and not `wdx`/`wdy`, which is the only channel
a wheel arrives on for the `imps2` protocol console-mouse.nix selects. A scroll wheel
parsed out of `mev` would be a scroll wheel that does not work.
"""

import os
import socket
import struct
from typing import NamedTuple, Protocol

# The daemon's control socket. A fixed path in gpm, not a compile-time option:
# `GPM_NODE_CTL` is `_PATH_DEV "gpmctl"` in src/headers/gpm.h.
GPM_SOCKET = "/dev/gpmctl"

# Event types, from `enum Gpm_Etype` in src/headers/gpm.h. Exactly one of the
# first four is set per event; everything from GPM_SINGLE down is a flag riding
# in the same field, which is why nothing here may compare `type` for equality
# without masking first.
GPM_MOVE = 1
GPM_DRAG = 2
GPM_DOWN = 4
GPM_UP = 8
GPM_SINGLE = 16
GPM_DOUBLE = 32
GPM_TRIPLE = 64
GPM_MFLAG = 128  # there was motion during the click
GPM_HARD = 256  # already handled by another client
GPM_ENTER = 512
GPM_LEAVE = 1024

# `#define GPM_BARE_EVENTS(type) ((type)&(0x0f|GPM_ENTER|GPM_LEAVE))`
GPM_BARE_EVENTS = 0x0F | GPM_ENTER | GPM_LEAVE

# Button bits. Note these are NOT in the order anyone expects -- right is the
# low bit -- and that the two wheel bits exist but are only set by the `ms3`
# protocol. For `imps2` a wheel notch arrives as an event with no buttons set
# and a non-zero `wdy`; see src/mice.c `M_imps2`.
GPM_B_NONE = 0
GPM_B_RIGHT = 1
GPM_B_MIDDLE = 2
GPM_B_LEFT = 4
GPM_B_FOURTH = 8
GPM_B_UP = 16
GPM_B_DOWN = 32

# struct Gpm_Connect { unsigned short eventMask, defaultMask, minMod, maxMod;
#                      int pid; int vc; }
#
# Every field is already naturally aligned at its standard offset, so the
# standard-size layout `=` and the compiler's native layout agree: 4 shorts at
# 0,2,4,6 then two ints at 8,12. 16 bytes.
_CONNECT = struct.Struct("=HHHHii")

# struct Gpm_Event { unsigned char buttons, modifiers; unsigned short vc;
#                    short dx, dy, x, y; enum Gpm_Etype type; int clicks;
#                    enum Gpm_Margin margin; short wdx, wdy; }
#
# The two enums are ints. Alignment works out the same way it does above:
# 1,1,2 then four shorts then three ints then two shorts. 28 bytes.
_EVENT = struct.Struct("=BBHhhhhiiihh")


class GpmEvent(NamedTuple):
    """One `Gpm_Event`, field for field.

    `x` and `y` are absolute console cells and are **1-based**, which is also what the
    TIOCLINUX selection ioctl wants, so nothing has to be adjusted between reading one
    and drawing the pointer at it.
    """

    buttons: int
    modifiers: int
    vc: int
    dx: int
    dy: int
    x: int
    y: int
    type: int
    clicks: int
    margin: int
    wdx: int
    wdy: int

    @property
    def bare_type(self) -> int:
        """The event type with the click-count and modifier flags masked off."""
        return self.type & GPM_BARE_EVENTS


def connect_payload(vc: int, event_mask: int, default_mask: int, pid: int) -> bytes:
    """The single `Gpm_Connect` a client writes after connecting.

    Split out from `GpmClient.connect` so the wire format can be checked without a
    daemon to talk to.
    """
    return _CONNECT.pack(
        event_mask,
        default_mask,
        0,  # minMod: no modifier required
        0xFFFF,  # maxMod: any modifier accepted
        pid,
        vc,
    )


class EventStream(Protocol):
    """The three socket methods `GpmClient` actually uses.

    Narrow on purpose: it is what lets the record-framing tests hand in a
    canned byte stream instead of standing up a daemon, without either a patch
    or a cast.
    """

    def recv(self, size: int, /) -> bytes:
        """Read at most `size` bytes."""

    def fileno(self) -> int:
        """The descriptor, for select()."""

    def close(self) -> None:
        """Let go of it."""


class GpmClient:
    """A registered connection to the gpm daemon for one virtual console."""

    def __init__(self, sock: EventStream) -> None:
        self._sock = sock
        self._buffer = b""

    @classmethod
    def connect(cls, vc: int, event_mask: int, default_mask: int) -> "GpmClient":
        """Register for events on virtual console `vc`.

        `event_mask` selects what is delivered here. `default_mask` selects what gpm's
        own handler keeps -- and the split is load-bearing rather than a tuning knob.
        Motion has to stay with the default handler because that handler *is* the
        pointer: `do_selection.c` draws it with `selection_copy(x,y,x,y,3)` on every
        GPM_MOVE. Buttons have to be taken away from it, or dragging across the console
        paints an inverse-video text selection over whatever tmux has drawn.

        gpm allows this connection from a non-root process only when the caller's uid
        owns /dev/tty<vc> (`src/daemon/processconn.c`); logind chowns tty1 to the
        operator at autologin, which is what lets the shim run as an ordinary user.
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(GPM_SOCKET)
            sock.sendall(connect_payload(vc, event_mask, default_mask, os.getpid()))
        except OSError:
            sock.close()
            raise
        return cls(sock)

    def fileno(self) -> int:
        return self._sock.fileno()

    def close(self) -> None:
        self._sock.close()

    def read_events(self) -> list[GpmEvent] | None:
        """Drain whatever has arrived.

        Returns None when the daemon has closed the connection, which the caller
        should treat as "no mouse from here on" rather than as an error: gpm
        restarting is not a reason to take the console session down.

        Short reads are real -- this is a stream socket, not a datagram one -- so a
        partial struct is held over to the next call and an empty *list* comes back.
        The two have to be distinguishable: answering both with `[]` meant the caller
        closed the socket on a short read, threw the held-over bytes away, and cost
        the operator the mouse for a reconnect interval -- and the carry-over below
        could never actually be exercised.
        """
        chunk = self._sock.recv(_EVENT.size * 64)
        if not chunk:
            return None
        self._buffer += chunk

        events: list[GpmEvent] = []
        size = _EVENT.size
        while len(self._buffer) >= size:
            events.append(GpmEvent(*_EVENT.unpack_from(self._buffer)))
            self._buffer = self._buffer[size:]
        return events
