"""The pty shim: tty1 on one side, the tmux client on the other.

Why a pty at all, rather than driving tmux over its command socket: because
tmux already knows how to route a mouse. Given real reports on its own
terminal it focuses the pane under the click, translates the position into
pane-relative coordinates, re-encodes the event in whatever protocol that
particular pane asked for -- btop wants SGR, opencode takes the legacy form --
drags borders, scrolls, and handles the status line. Reimplementing that
against `send-keys` would be several times this much code doing a worse job.

So the shim becomes the terminal. It is deliberately thin: bytes from the
console go to the pty, bytes from the pty go to the console, gpm events become
SGR reports written into the pty, and the pointer is bracketed around every
write (see `pointer`).

Failure is always the same shape -- `exec` the tmux command and get out of the
way. The console session is the appliance's only user interface and there is no
remote access to repair it with, so the worst this is allowed to cost is the
mouse.
"""

import errno
import fcntl
import os
import select
import signal
import struct
import sys
import termios
import time
import tty
from typing import NoReturn

from loom_console_mouse.gpm import (
    GPM_DOWN,
    GPM_DRAG,
    GPM_HARD,
    GPM_MOVE,
    GPM_UP,
    GpmClient,
)
from loom_console_mouse.pointer import Pointer
from loom_console_mouse.sgr import PointerState, translate

# What is asked of gpm, and what is left to gpm.
#
# Motion stays in the default mask because gpm's default handler *is* the
# pointer -- `do_selection.c` draws it on every GPM_MOVE. Buttons are
# deliberately not in it: gpm's default handler treats those as text selection
# and paste, which on a console tmux is drawing would paint an inverse-video
# selection across the panes and, on button 2, try to paste into them.
_EVENT_MASK = GPM_MOVE | GPM_DRAG | GPM_DOWN | GPM_UP
_DEFAULT_MASK = GPM_MOVE

# How often a pure-motion report may be sent, in seconds.
#
# btop asks for `?1003` (any-motion tracking), so tmux forwards every motion
# event into it, and gpm will happily produce one per mouse interrupt. 60 Hz is
# smooth to a human and keeps a busy pane from being handed thousands of escape
# sequences a second. Presses, releases, drags and wheel notches are never
# coalesced -- only motion with no button down.
_MOTION_INTERVAL = 1.0 / 60.0

# How long to wait before trying gpm again after losing it.
#
# Losing it is a routine event, not a fault: console-mouse.nix restarts gpm
# when the console is resized by a DRM takeover, because gpm's own SIGWINCH
# path crashes. Without a retry the mouse would be dead for the life of a
# session that happened to start before that.
_RECONNECT_INTERVAL = 2.0

_IO_CHUNK = 65536


def _exec(argv: list[str]) -> NoReturn:
    """Become the wrapped command. The one exit from every failure path."""
    os.execvp(argv[0], argv)


def _console_vc(fd: int) -> int | None:
    """The virtual console number behind `fd`, or None if it is not a VT.

    Read off the tty name rather than assumed to be 1. console.nix gates the
    session on /dev/tty1 today, but a shim that hardcoded that would register
    with gpm for the wrong console the moment anything moved -- and gpm
    delivers events only for the console a client asked for, so the failure
    would be a mouse that does nothing, with no error anywhere.
    """
    try:
        name = os.ttyname(fd)
    except OSError:
        return None
    prefix = "/dev/tty"
    if not name.startswith(prefix):
        return None
    suffix = name[len(prefix) :]
    if not suffix.isdigit():
        # /dev/tty, /dev/ttyS0, /dev/ttyUSB0: the controlling-terminal alias or
        # a serial line. Neither has a gpm console behind it, and a serial
        # client is talking to a real terminal emulator that does its own mouse
        # reporting anyway -- see vm-serial.nix.
        return None
    return int(suffix)


def _window_size(fd: int) -> bytes:
    try:
        return fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8)
    except OSError:
        # 24x80, in struct winsize order (rows, cols, xpixel, ypixel).
        return struct.pack("HHHH", 24, 80, 0, 0)


def _set_window_size(fd: int, size: bytes) -> None:
    try:
        fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
    except OSError:
        pass


def _write_all(fd: int, data: bytes) -> None:
    while data:
        try:
            written = os.write(fd, data)
        except OSError as exc:
            if exc.errno == errno.EINTR:
                continue
            raise
        data = data[written:]


class Relay:
    """One console, one pty, one gpm connection."""

    def __init__(self, console_fd: int, gpm: GpmClient, master: int, vc: int) -> None:
        self._console = console_fd
        self._gpm: GpmClient | None = gpm
        self._vc = vc
        self._master = master
        self._pointer = Pointer(console_fd)
        self._state = PointerState.initial()
        self._pending_motion = b""
        self._next_motion_at = 0.0
        self._reconnect_at = 0.0

    def close(self) -> None:
        """Take the pointer down.

        Called before the terminal is handed back, or the kernel is left
        holding a cached cell for a pointer that nothing will ever move again
        -- and the next thing to complement that cell would restore it.
        """
        self._pointer.hide()

    def _to_console(self, data: bytes) -> None:
        """Write to the console with the pointer taken down around it.

        This ordering is the reason the shim exists in this shape rather than
        beside the session. See `pointer` for what the kernel does with the
        cell underneath.
        """
        self._pointer.hide()
        _write_all(self._console, data)
        self._pointer.show()

    def _drop_gpm(self) -> None:
        """Carry on without a mouse, and arrange to get it back.

        A console session that died because a mouse daemon restarted would be
        a much worse bug than the one this package exists to fix -- and gpm
        restarting is expected here rather than exceptional, since that is how
        console-mouse.nix makes it re-read the console size.
        """
        if self._gpm is not None:
            self._gpm.close()
            self._gpm = None
        self._pointer.hide()
        self._reconnect_at = time.monotonic() + _RECONNECT_INTERVAL

    def _reconnect_gpm(self, now: float) -> None:
        if self._gpm is not None or now < self._reconnect_at:
            return
        self._reconnect_at = now + _RECONNECT_INTERVAL
        try:
            self._gpm = GpmClient.connect(self._vc, _EVENT_MASK, _DEFAULT_MASK)
        except OSError:
            return
        # The daemon that comes back knows nothing about where the pointer was,
        # and on the path this exists for the console has just been resized
        # under it, so the old position may not even be on screen any more.
        self._state = PointerState.initial()

    def _handle_gpm(self) -> None:
        assert self._gpm is not None
        try:
            events = self._gpm.read_events()
        except OSError:
            events = []
        if not events:
            self._drop_gpm()
            return

        for event in events:
            # gpm sets GPM_HARD on an event it has already passed to another
            # handler. Nothing else consumes this console today, but honouring
            # the flag costs one line and prevents a duplicate report if that
            # ever changes.
            if event.type & GPM_HARD:
                continue

            translation = translate(event, self._state)
            self._state = translation.state

            if translation.moved:
                self._pointer.move(translation.state.x, translation.state.y)

            if not translation.report:
                continue

            if event.bare_type == GPM_MOVE:
                # Pure motion: coalesce. Keeping only the newest report is
                # correct because each carries an absolute position, so a
                # dropped one is genuinely redundant.
                self._pending_motion = translation.report
                continue

            # Anything the operator did deliberately goes out at once, and
            # supersedes a motion report that has not been sent -- the position
            # it carried is already in this one.
            self._pending_motion = b""
            _write_all(self._master, translation.report)

    def _flush_motion(self, now: float) -> None:
        if not self._pending_motion or now < self._next_motion_at:
            return
        _write_all(self._master, self._pending_motion)
        self._pending_motion = b""
        self._next_motion_at = now + _MOTION_INTERVAL

    def run(self, wakeup_read: int) -> None:
        """Pump until the child on the other end of the pty exits."""
        while True:
            readable = [self._console, self._master, wakeup_read]
            if self._gpm is not None:
                readable.append(self._gpm.fileno())

            # Wake up for whichever is due first: a coalesced motion report, or
            # the next attempt at a gpm that has gone away. Neither is urgent,
            # and with neither pending this blocks until something happens.
            timeout: float | None = None
            if self._pending_motion:
                timeout = _MOTION_INTERVAL
            if self._gpm is None:
                pending = max(0.0, self._reconnect_at - time.monotonic())
                timeout = pending if timeout is None else min(timeout, pending)

            try:
                ready, _, _ = select.select(readable, [], [], timeout)
            except InterruptedError:
                continue
            except OSError as exc:
                if exc.errno == errno.EINTR:
                    continue
                raise

            if wakeup_read in ready:
                # A signal arrived. The only one installed is SIGWINCH, and the
                # answer is always the same: the console changed size, so the
                # pty must follow. This process is in tty1's foreground process
                # group, so unlike gpm it actually receives it.
                try:
                    os.read(wakeup_read, _IO_CHUNK)
                except OSError:
                    pass
                _set_window_size(self._master, _window_size(self._console))

            if self._console in ready:
                try:
                    data = os.read(self._console, _IO_CHUNK)
                except OSError:
                    data = b""
                if data:
                    _write_all(self._master, data)

            if self._gpm is not None and self._gpm.fileno() in ready:
                self._handle_gpm()

            if self._master in ready:
                try:
                    data = os.read(self._master, _IO_CHUNK)
                except OSError as exc:
                    # EIO on a pty master is how Linux reports "the last slave
                    # was closed", which is the normal way this loop ends.
                    if exc.errno not in (errno.EIO, errno.EINTR):
                        raise
                    data = b""
                if not data:
                    return
                self._to_console(data)

            now = time.monotonic()
            self._flush_motion(now)
            self._reconnect_gpm(now)


def run(argv: list[str]) -> int:
    """Run `argv` under the shim. Returns its exit status.

    Every reason the shim cannot do its job ends in `_exec(argv)` rather than
    in an exception, so the operator gets the session they would have had
    anyway.
    """
    console_fd = 0
    if not os.isatty(console_fd):
        _exec(argv)

    vc = _console_vc(console_fd)
    if vc is None:
        _exec(argv)

    try:
        gpm = GpmClient.connect(vc, _EVENT_MASK, _DEFAULT_MASK)
    except OSError:
        # No daemon, no socket, or no permission. console-mouse.nix orders gpm
        # long before anyone can log in, so in practice this is the
        # `loom.consoleMouse.enable = false` build -- which has to behave
        # exactly like the session did before any of this existed.
        _exec(argv)

    master, slave = os.openpty()
    _set_window_size(master, _window_size(console_fd))

    child = os.fork()
    if child == 0:
        os.close(master)
        gpm.close()
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        for target in (0, 1, 2):
            os.dup2(slave, target)
        if slave > 2:
            os.close(slave)
        _exec(argv)

    os.close(slave)

    # A self-pipe rather than a flag set in the handler: select() has to be
    # woken, and PEP 475 restarts it after running the handler, so a plain flag
    # would not be noticed until the next unrelated event.
    wakeup_read, wakeup_write = os.pipe()
    os.set_blocking(wakeup_read, False)
    os.set_blocking(wakeup_write, False)
    signal.set_wakeup_fd(wakeup_write)
    signal.signal(signal.SIGWINCH, lambda _signum, _frame: None)

    saved = termios.tcgetattr(console_fd)
    relay = Relay(console_fd, gpm, master, vc)
    try:
        tty.setraw(console_fd)
        relay.run(wakeup_read)
    finally:
        relay.close()
        termios.tcsetattr(console_fd, termios.TCSAFLUSH, saved)
        signal.set_wakeup_fd(-1)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        os.close(master)
        os.close(wakeup_read)
        os.close(wakeup_write)

    _, status = os.waitpid(child, 0)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    # `--` so the wrapped command's own flags are never mistaken for the
    # shim's. console.nix always passes it.
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        print("usage: loom-console-mouse -- COMMAND [ARG...]", file=sys.stderr)
        return 2
    return run(args)
