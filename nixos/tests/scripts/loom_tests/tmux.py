"""The operator's tmux session, as the tests see it.

console.nix builds one session on tty1 and three tests have something to ask of it: the
mouse test clicks on panes, the appliance test asserts what each pane runs, and the
readiness test reads the status line. They asked in three different ways -- two of them
parsing `list-panes` output inline, all three with their own copy of the socket path --
because while the scripts were concatenated rather than imported, this could not be
shared. It came from loom_tests/mouse.py, which is where it grew up.

`Session` deliberately holds a machine rather than being a set of functions taking one:
every method is a command against the same server on the same box, and threading the
machine through each call obscured that.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from loom_tests.driver import Machine

# console.nix's `loom.consoleSocket`. A fixed path rather than $XDG_RUNTIME_DIR, for the
# reason given there; tests/appliance.nix asserts this constant still matches the option,
# which is the check that makes one copy of the path safe to keep here.
SOCKET = "/run/loom/tmux.sock"

SESSION = "loom"


class Pane(NamedTuple):
    """One pane, as tmux reports it.

    The geometry is what makes a click testable: a console cell is turned into the pane
    that covers it, and that pane is what the focus is then asserted on.
    """

    id: str
    left: int
    top: int
    right: int
    bottom: int
    active: bool
    command: str

    def covers(self, col: int, row: int) -> bool:
        return self.left <= col <= self.right and self.top <= row <= self.bottom


class Session:
    """The operator's tmux session, and whatever is pointed at it."""

    def __init__(self, machine: "Machine") -> None:
        self.machine = machine

    def tmux(self, command: str) -> str:
        return self.machine.succeed(f"tmux -S {SOCKET} {command}").strip()

    def option(self, name: str) -> str:
        """One global option's value, for the assertions about the status line."""
        return self.tmux(f"show-options -gv {name}")

    def panes(self) -> list[Pane]:
        """Every pane of the session, in layout order.

        `pane_start_command`, not `pane_current_command`: loom-btop execs btop, so the
        current command is whatever that wrapper turned into. What the tests assert is
        how the session is wired, which is the command it was started with.
        """
        raw = self.tmux(
            "list-panes -t " + SESSION + " -F "
            "'#{pane_id} #{pane_left} #{pane_top} #{pane_right} "
            "#{pane_bottom} #{pane_active} #{pane_start_command}'"
        )
        out = []
        for line in raw.splitlines():
            pane_id, left, top, right, bottom, active, command = line.split(" ", 6)
            out.append(
                Pane(
                    id=pane_id,
                    left=int(left),
                    top=int(top),
                    right=int(right),
                    bottom=int(bottom),
                    active=active == "1",
                    command=command,
                )
            )
        return out

    def pane_covering(self, col: int, row: int) -> Pane | None:
        """The pane containing a zero-based console cell, or None."""
        for pane in self.panes():
            if pane.covers(col, row):
                return pane
        return None

    def active_pane(self) -> Pane:
        for pane in self.panes():
            if pane.active:
                return pane
        raise AssertionError("no active pane")

    def mouse(self, *commands: str) -> None:
        self.machine.succeed("loom-fake-mouse " + " ".join(commands))

    def wait_until_focused(self, pane: Pane) -> None:
        self.machine.wait_until_succeeds(
            f"tmux -S {SOCKET} display -p -t {pane.id} '#{{pane_active}}'"
            " | grep -qx 1"
        )
