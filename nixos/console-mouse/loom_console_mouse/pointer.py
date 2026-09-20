"""Drawing gpm's pointer without leaving stale characters behind.

The pointer on a Linux console is one character cell drawn in reverse video,
and the kernel does the drawing: `TIOCL_SETSEL` with `sel_mode` of
`TIOCL_SELPOINTER` lands in `highlight_pointer()` and then `complement_pos()`
in drivers/tty/vt/vt.c. That function is worth reading before changing
anything here:

    static int old_offset = -1;
    static unsigned short old;
    ...
    if (old_offset != -1 && ...)
            scr_writew(old, screenpos(vc, old_offset, true));   // put it back
    old_offset = offset;
    if (offset != -1 && ...) {
            old = scr_readw(p);                                 // remember it
            scr_writew(old ^ vc->vc_complement_mask, p);
    }

It caches the character *and* its attribute, and writes that cache back when
the pointer next moves. So if anything repaints the cell while the pointer is
sitting on it -- btop and k9s repaint continuously -- the next mouse movement
restores a character that has not been true for seconds, on top of live output.
tmux never reads the screen back, so nothing repairs it.

The fix is to never let the cache go stale: clear the pointer before writing to
the console, write, then put it back. `hide()` around every write is why this
shim has to own the output stream rather than sit beside it.

Both of the sel_modes used here are explicitly exempted from CAP_SYS_ADMIN by
`set_selection_user()` ("TIOCL_SELCLEAR and TIOCL_SELPOINTER are OK to use
without CAP_SYS_ADMIN as they do not modify the selection"), which is what lets
the shim run as the operator rather than as root. The ioctl does still require
the caller's controlling terminal to be the tty it is issued on, so this must
be handed the console fd and not, say, the pty.
"""

import fcntl
import struct

# linux/tiocl.h
TIOCL_SETSEL = 2
TIOCL_SELPOINTER = 3
TIOCL_SELCLEAR = 4

# asm-generic/ioctls.h. Not in Python's termios module on every platform, so
# spelled out.
TIOCLINUX = 0x541C

# `tioclinux()` reads the subcode from the first byte of the argument and hands
# `arg + 1` to `set_selection_user()` as a `struct tiocl_selection`
# (drivers/tty/vt/vt.c). Hence one byte, then five unaligned shorts -- the
# kernel copies the struct with `copy_from_user`, so the misalignment is fine,
# and gpm's own `selection_copy()` builds exactly this shape.
_SETSEL = struct.Struct("=B5H")


class Pointer:
    """The console pointer, kept in step with whatever is being written."""

    def __init__(self, console_fd: int) -> None:
        self._fd = console_fd
        self._x = 0
        self._y = 0
        self._shown = False

    def _setsel(self, xs: int, ys: int, xe: int, ye: int, mode: int) -> None:
        # Best effort throughout. A console that will not take the ioctl -- a
        # pty, a serial line, a kernel built without console selection -- costs
        # the pointer and nothing else, and must never take the operator's
        # session down with it.
        try:
            fcntl.ioctl(
                self._fd, TIOCLINUX, _SETSEL.pack(TIOCL_SETSEL, xs, ys, xe, ye, mode)
            )
        except OSError:
            pass

    def move(self, x: int, y: int) -> None:
        """Remember where the pointer is, and draw it there."""
        self._x, self._y = x, y
        self.show()

    def show(self) -> None:
        """Draw the pointer at the last known position."""
        if self._x <= 0 or self._y <= 0:
            return
        self._setsel(self._x, self._y, self._x, self._y, TIOCL_SELPOINTER)
        self._shown = True

    def hide(self) -> None:
        """Undraw it, restoring the cell underneath from the kernel's cache.

        Called before every write to the console. Doing it the other way round
        -- write first, redraw after -- would leave the cache holding the cell
        as it was *before* the write, which is the whole failure this exists to
        prevent.
        """
        if not self._shown:
            return
        self._setsel(0, 0, 0, 0, TIOCL_SELCLEAR)
        self._shown = False
