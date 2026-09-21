"""The two plain-text renderings, and the characters they are not allowed to contain.

Both of these leave Python and are interpreted by something else -- agetty, which reads
the banner line out of an issue file, and tmux, which re-expands the status segment. Each
has a character that would be silently eaten or silently misread, and neither failure
shows up anywhere but on the screen of a box somebody has already driven to.
"""

from loom_ready.state import Counts, Readiness, Stage
from loom_ready.text import STALL_AFTER_S, oneline, stall_note, summary, tmux_oneline


def readiness(stage: Stage, ready: int = 0, total: int = 0, **extra) -> Readiness:
    return Readiness(
        stage=stage, counts=Counts(ready=ready, total=total), updated=1000.0, **extra
    )


def test_every_banner_line_is_one_agetty_will_not_eat():
    """A backslash in an issue file is an agetty escape, consumed before anyone sees it.

    box.nix says so at the top of the banner generator, and the passphrase charset and
    the WiFi credentials are both constrained by it. This is the same rule for the same
    file.
    """
    for stage in Stage:
        line = summary(readiness(stage, ready=3, total=7))
        assert "\\" not in line, stage
        assert "\n" not in line, stage
        assert line.isascii(), stage


def test_waiting_costs_the_banner_no_row_at_all():
    """The banner is the one screen here with a hard height budget.

    It goes straight to the VT with no paging, so a line too many scrolls the Loom mark
    off the top -- and on a --wifi box a QR code is already competing for the same rows.
    "waiting for the cluster" is what every boot says for its first minute, before
    anybody has walked up, and is the one stage a reader cannot act on.
    """
    assert summary(readiness(Stage.WAITING)) == ""
    # Every other stage does earn its row, including the two that report trouble.
    for stage in Stage:
        if stage is not Stage.WAITING:
            assert summary(readiness(stage, ready=3, total=7)), stage


def test_the_status_line_still_speaks_while_the_cluster_does_not():
    """One row, no budget, and "nothing at all" would read as a broken status line."""
    assert oneline(readiness(Stage.WAITING)) == "starting"


def test_every_stage_has_a_status_segment_tmux_will_not_misread():
    """tmux re-expands `#()` output, so a bare hash would start a format directive."""
    for stage in Stage:
        segment = oneline(readiness(stage, ready=3, total=7))
        assert segment
        assert "#" not in segment, stage
        assert "\n" not in segment, stage
        # It shares a row with "Alt-F2 for a shell" and two clickable controls.
        assert len(segment) <= 24, segment


def test_nothing_published_says_nothing_at_all():
    """A setup-mode box, or the first seconds of a boot.

    Both readers treat the empty string as "draw the screen the way it looked before any
    of this existed", which is what makes this feature safe to add to a banner that is
    already close to the height of a small console.
    """
    assert summary(None) == ""
    assert oneline(None) == ""
    assert tmux_oneline(None) == ""


def test_a_ready_box_says_so_without_arithmetic():
    """Nobody standing at a working box wants to read 18/18."""
    assert summary(readiness(Stage.READY, ready=18, total=18)) == "Loom: ready."
    assert oneline(readiness(Stage.READY, ready=18, total=18)) == "ready"


def test_a_starting_box_carries_its_numbers():
    line = summary(readiness(Stage.ROLLING_OUT, ready=12, total=18))
    assert "12/18" in line
    assert "pods" in line


def test_a_namespace_with_nothing_in_it_yet_does_not_show_a_ratio():
    """0/0 is not "nothing to do", and must never be drawn as though it were.

    This is the window up.sh spends creating the namespace before applying anything into
    it, and a bar reading 0/0 is one a renderer would happily call complete.
    """
    line = summary(readiness(Stage.DEPLOYING))
    assert "0/0" not in line, line
    assert "no workloads yet" in line, line


def test_the_status_segment_is_styled_for_the_stage():
    """The colour is the fastest thing to read across a room."""
    green = tmux_oneline(readiness(Stage.READY))
    assert green.startswith("#[fg=green]")
    assert green.endswith("#[default]")
    assert "ready" in green
    assert "red" in tmux_oneline(readiness(Stage.DEGRADED, ready=17, total=18))


def test_the_stall_note_waits_before_it_says_anything():
    """A container image pull is slow, not stuck, and must not be called stuck."""
    record = readiness(Stage.ROLLING_OUT, ready=3, total=7, changed=1000.0)
    assert stall_note(record, now=1000.0 + STALL_AFTER_S - 1) == ""
    assert stall_note(record, now=1000.0 + STALL_AFTER_S) == "no change for 5m"
    assert stall_note(record, now=1000.0 + 3600 + 120) == "no change for 1h02m"


def test_a_ready_box_is_never_stalled():
    """Nothing is supposed to be moving."""
    record = readiness(Stage.READY, ready=7, total=7, changed=1.0)
    assert stall_note(record, now=100000.0) == ""


def test_a_degraded_box_still_reports_its_numbers():
    """ "degraded" alone does not say whether one pod is down or seventeen."""
    line = summary(readiness(Stage.DEGRADED, ready=17, total=18))
    assert "degraded" in line
    assert "17/18" in line
