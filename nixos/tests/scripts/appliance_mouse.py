"""Point-and-click on the console session, end to end.

A uinput mouse in the guest, through mousedev and gpm and the pty shim, to the pane tmux
focuses. The pure halves are unit-tested inside the `loom-console-mouse` derivation
(nixos/console-mouse/tests); this is the part that only fails on a booted machine.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from driver import Machine, StartAll, Subtest

SOCKET = "/run/loom/tmux.sock"

# Far enough to clamp at any console size this box will ever have.
FAR = 30000


class Params(NamedTuple):
    """What the .nix file knows and this file cannot."""

    operator: str


class Pane(NamedTuple):
    """One pane, as tmux reports it.

    The geometry is what makes a click testable: a console cell is turned into the
    pane that covers it, and that pane is what the focus is then asserted on.
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
    """The operator's tmux session, and the mouse pointed at it."""

    def __init__(self, appliance: "Machine") -> None:
        self.appliance = appliance

    def tmux(self, command: str) -> str:
        return self.appliance.succeed(f"tmux -S {SOCKET} {command}").strip()

    def panes(self) -> list[Pane]:
        raw = self.tmux(
            "list-panes -t loom -F "
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
        self.appliance.succeed("loom-fake-mouse " + " ".join(commands))

    def wait_until_focused(self, pane: Pane) -> None:
        self.appliance.wait_until_succeeds(
            f"tmux -S {SOCKET} display -p -t {pane.id} '#{{pane_active}}'"
            " | grep -qx 1"
        )


def _gpm_survives_resize(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("gpm runs, and survives the console being resized"):
        appliance.wait_for_unit("gpm.service")

        # The ordering that keeps gpm's one-shot console measurement honest.
        # Asserted on the unit rather than observed, because a test VM's console
        # does not go through the four resizes a real panel does -- see
        # branding.nix. Getting this wrong clamps the pointer to a fraction of the
        # screen on the box and nowhere else.
        ordering = appliance.succeed(
            "systemctl show --property=After --value gpm.service"
        )
        assert "loom-console-font.service" in ordering, ordering

        # The regression this subtest exists for.
        #
        # loom-console-font-reapply fires from a udev rule when the DRM driver takes
        # the console, and it has to make gpm re-read the size. Signalling it does
        # not work: gpm's SIGWINCH path segfaults, which is unsurprising once you
        # notice nothing ever sends a daemon that signal, so the path is dead code
        # upstream. console-mouse.nix restarts the unit instead -- and the proof is
        # that gpm is still alive after the reapply has run, not that the config
        # says so.
        appliance.wait_until_succeeds(
            "systemctl show --property=Result --value"
            " loom-console-font-reapply.service | grep -qx success"
        )
        appliance.succeed("systemctl is-active gpm.service")
        assert "core-dump" not in appliance.succeed(
            "systemctl show --property=Result --value gpm.service"
        )

        # mousedev, not an evdev node: /dev/input/mice multiplexes every mouse,
        # which is what makes one plugged in after boot work.
        appliance.succeed("test -c /dev/input/mice")


def _session_runs_under_the_shim(
    session: Session, subtest: "Subtest", params: Params
) -> None:
    appliance = session.appliance
    with subtest("a keypress opens the session, under the shim"):
        fg = appliance.succeed("fgconsole").strip()
        assert fg == "1", f"foreground console is {fg}, not tty1"

        appliance.send_key("ret")
        appliance.wait_until_succeeds(f"pgrep -u {params.operator} -f tmux")

        # The shim has to be between the console and the tmux client, not beside it:
        # being in the output stream is the only place the pointer can be drawn
        # without leaving stale cells behind.
        appliance.wait_until_succeeds(
            f"pgrep -u {params.operator} -f loom-console-mouse"
        )

        # Asserted on the client's controlling terminal, which is the observable
        # consequence: without the shim the client sits on /dev/tty1, exactly as
        # this session used to run, and a pts means something allocated a pty and
        # put itself in the middle.
        #
        # The client is identified by asking tmux rather than by pgrep, because the
        # shim's own command line *is* the tmux command line -- it was handed
        # `... tmux ... attach-session -t loom` to run -- so any pattern that
        # matches the client matches the shim too, and the shim is legitimately on
        # tty1. It has to be: the ioctl that draws the pointer only works from a
        # process whose controlling terminal is the console it is drawing on.
        appliance.wait_until_succeeds(
            f"tmux -S {SOCKET} list-clients -t loom | grep -q ."
        )
        client = int(session.tmux("list-clients -t loom -F '#{client_pid}'"))
        terminal = appliance.succeed(f"ps -o tty= -p {client}").strip()
        assert terminal.startswith("pts/"), (
            f"the tmux client is on {terminal}, so nothing is between it "
            "and the console"
        )


def _click_focuses_top_left(session: Session, subtest: "Subtest") -> None:
    with subtest("clicking the top-left pane focuses it"):
        session.mouse(f"move:-{FAR},-{FAR}")
        target = session.pane_covering(0, 0)
        assert target is not None, session.panes()
        session.mouse("click:")
        session.wait_until_focused(target)


def _click_moves_focus(session: Session, subtest: "Subtest", cols: int) -> None:
    with subtest("clicking the top-right pane moves the focus there"):
        # A different pane from the one above, which is what makes this a test of
        # the click rather than of the starting state.
        session.mouse(f"move:{FAR},0")
        target = session.pane_covering(cols - 1, 0)
        assert target is not None, session.panes()
        assert not target.active, "already focused before the click"
        session.mouse("click:")
        session.wait_until_focused(target)
        assert "btop" in session.active_pane().command, session.active_pane()


def _mouse_reaches_into_the_pane(session: Session, subtest: "Subtest") -> None:
    with subtest("the mouse reaches into a pane, not just onto it"):
        # btop asks for ?1002/?1003/?1006 -- it wants motion as well as clicks --
        # and tmux only forwards what its own terminal sends it. `mouse_any_flag` is
        # tmux's record of the pane having asked, so a true value here is tmux
        # saying it will route events inward.
        session.appliance.wait_until_succeeds(
            f"tmux -S {SOCKET} display -p -t {session.active_pane().id}"
            " '#{mouse_any_flag}' | grep -qx 1"
        )


def _k9s_accepts_the_mouse(
    session: Session, subtest: "Subtest", params: Params
) -> None:
    with subtest("k9s is configured to accept the mouse"):
        # tcell can do every mouse mode, but k9s gates them behind ui.enableMouse,
        # which defaults off -- so without this the pods pane is the one place a
        # click does nothing.
        #
        # Run rather than read off the store, because what matters is the file
        # loom-k9s actually writes. It cannot be observed in the pane here: the log
        # pane only hands over to k9s once the namespace exists, and no cluster ever
        # comes up in a test VM. So the command is invoked directly -- as the
        # operator, or the config directory would end up owned by root -- and killed
        # once it starts waiting for that same cluster. It writes its config before
        # the wait for exactly this kind of reason.
        session.appliance.succeed(
            f"su {params.operator} -s /bin/sh -c 'timeout 5 loom-k9s'"
            " >/dev/null 2>&1 || true"
        )
        config = session.appliance.succeed("cat /run/loom/k9s/config.yaml")
        assert "enableMouse: true" in config, config


def _prefix_is_unreachable(session: Session, subtest: "Subtest") -> None:
    with subtest("the prefix is unreachable from the keyboard"):
        # `prefix None` rather than `unbind-key -a`, because every mouse behaviour
        # tmux has lives in the root table as an ordinary binding -- unbinding
        # everything would have removed the feature above.
        assert session.tmux("show-options -g prefix") == "prefix None"
        assert session.tmux("show-options -g prefix2") == "prefix2 None"

        # And the menus a right-click would otherwise open, which carry Kill,
        # Respawn, Split, New Session and a command prompt.
        root_keys = session.tmux("list-keys -T root")
        assert "MouseDown3" not in root_keys, root_keys

        # The proof rather than the configuration: Ctrl-b d is what used to detach,
        # and the session must still have its client afterwards.
        session.appliance.send_key("ctrl-b")
        session.appliance.send_chars("d")
        session.appliance.sleep(2)
        attached = session.tmux("list-clients -t loom | wc -l")
        assert attached != "0", "Ctrl-b d detached the session"


def _status_line_detaches(session: Session, subtest: "Subtest") -> None:
    with subtest("clicking the status line detaches"):
        # The controls are drawn flush against the right-hand edge precisely so that
        # the bottom-right corner of the screen lands inside the detach range -- and
        # so that an operator has the easiest target on the display.
        session.mouse(f"move:{FAR},{FAR}")
        session.mouse("click:")
        session.appliance.wait_until_succeeds(
            f"tmux -S {SOCKET} list-clients -t loom | wc -l | grep -qx 0"
        )

        # Detaching is meant to hand the box back to the banner: the client exits,
        # the shim exits with it, loom-console returns 0 and the login shell leaves,
        # so agetty comes back round.
        session.appliance.wait_until_succeeds("pgrep -f 'agetty.*tty1'")


def run(
    appliance: "Machine", *, start_all: "StartAll", subtest: "Subtest", params: Params
) -> None:
    """The whole test, as the .nix file calls it."""
    start_all()
    appliance.wait_for_unit("multi-user.target")
    session = Session(appliance)

    _gpm_survives_resize(appliance, subtest)
    _session_runs_under_the_shim(session, subtest, params)

    # Wait for the layout to stop moving. `create` respawns panes after the last
    # split, and a click landing mid-respawn would be testing nothing.
    appliance.wait_until_succeeds(
        f"tmux -S {SOCKET} list-panes -t loom | wc -l | grep -qvx 0"
    )
    _, cols = (
        int(value) for value in appliance.succeed("stty size < /dev/tty1").split()
    )

    _click_focuses_top_left(session, subtest)
    _click_moves_focus(session, subtest, cols)
    _mouse_reaches_into_the_pane(session, subtest)
    _k9s_accepts_the_mouse(session, subtest, params)
    _prefix_is_unreachable(session, subtest)
    _status_line_detaches(session, subtest)
