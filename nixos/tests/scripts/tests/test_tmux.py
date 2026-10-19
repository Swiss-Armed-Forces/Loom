"""Reading the operator's session out of tmux.

Two things here are worth a test that does not boot a machine. The format string is one:
`panes()` asks for seven fields and unpacks seven, and a mismatch is a `ValueError` deep
inside a VM test that was asserting something else entirely. The geometry is the other
-- `covers` is what turns a console cell into the pane a click landed in, and an off-by-
one at a pane border is exactly the bug the mouse test exists to catch, so it must not
be in the test's own helper.
"""

import machines
import pytest

from loom_tests import tmux

# Three panes as console.nix lays them out on an 80x25 VT: the log and btop along the
# top, the assistant full width underneath, and the status line on the last row.
LISTING = "\n".join(
    [
        "%0 0 0 39 9 0 loom-progress",
        "%1 41 0 79 9 0 loom-btop",
        "%2 0 11 79 23 1 loom-chat",
    ]
)


def session(listing: str = LISTING) -> tmux.Session:
    return tmux.Session(
        machines.as_machine(machines.FakeMachine({"list-panes": listing}))
    )


def test_every_pane_comes_back_with_its_geometry_and_command():
    panes = session().panes()
    assert [pane.id for pane in panes] == ["%0", "%1", "%2"]
    assert panes[0].command == "loom-progress"
    assert (panes[2].left, panes[2].top, panes[2].right, panes[2].bottom) == (
        0,
        11,
        79,
        23,
    )


def test_a_command_with_arguments_survives_the_split():
    """Every pane runs under loom-pane, so the command is never one word.

    `split(" ", 6)` is what keeps the rest of the line whole; a plain split would take
    the store path of the supervised program for a geometry field.
    """
    supervised = (
        "%0 0 0 39 9 0 /nix/store/abc-loom-pane/bin/loom-pane"
        " /nix/store/x-loom-progress"
    )
    pane = session(supervised).panes()[0]
    assert pane.command.endswith("x-loom-progress")
    assert pane.right == 39


def test_the_active_pane_is_the_one_tmux_flagged():
    assert session().active_pane().id == "%2"


def test_a_session_with_no_active_pane_is_an_error_here():
    """Rather than a None that fails two assertions later with no explanation."""
    with pytest.raises(AssertionError):
        session("%0 0 0 39 9 0 loom-progress").active_pane()


def test_a_cell_maps_to_the_pane_that_covers_it():
    assert session().pane_covering(0, 0).id == "%0"
    assert session().pane_covering(50, 5).id == "%1"
    assert session().pane_covering(50, 20).id == "%2"


def test_pane_borders_belong_to_the_pane_on_both_edges():
    """`covers` is inclusive, and the mouse test clicks corners on purpose."""
    top_left = session().panes()[0]
    assert top_left.covers(0, 0)
    assert top_left.covers(39, 9)
    assert not top_left.covers(40, 9)
    assert not top_left.covers(39, 10)


def test_a_cell_in_no_pane_is_none():
    """The status line row, which is tmux's own and not part of any pane."""
    assert session().pane_covering(0, 24) is None


def test_every_command_names_the_socket_and_the_session():
    """One copy of this path now; three tests used to carry their own.

    tests/appliance.nix asserts the constant against console.nix's `loom.consoleSocket`
    on a booted box, which is what makes keeping it here safe. What is checked here is
    that the commands actually use it -- a default socket would find the *test driver's*
    tmux, if it had one, rather than the operator's session.
    """
    talker = session()
    talker.panes()
    assert talker.machine.calls[0].startswith(f"tmux -S {tmux.SOCKET} list-panes")
    assert f"-t {tmux.SESSION}" in talker.machine.calls[0]
