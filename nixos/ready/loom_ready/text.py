"""The two plain-text renderings, away from anything that knows about rich.

Both are consumed by something that is not a Python program -- a shell script assembling
an agetty issue file, and a tmux status line -- so both are ordinary strings with rules
about what may be in them:

  * ASCII, and no backslash. agetty reads a backslash in an issue file as the start of an
    escape of its own and eats it before anyone sees it (box.nix:84-88). The banner's
    charset has been a real constraint since the QR code went in.
  * No `#`. tmux re-expands the output of a `#()` command, so a stray hash in the status
    segment would be read as the start of a format directive.
  * One line. `loom-info` prints the summary with a single `printf`, and a status line is
    a line.

tests/test_text.py asserts all three against every stage, which is cheaper than finding
out on a box in a room somebody had to drive to.
"""

from loom_ready.state import Readiness, Stage

# What the counts are counted in. They are desired replicas, and a desired replica is a
# pod that ought to exist -- which is the noun an operator standing at the box uses.
UNIT = "pods"

# Long enough that an image pull is not called stuck, short enough to notice within one
# coffee. Only ever shown, never a stage.
STALL_AFTER_S = 300.0

STAGE_WORD = {
    Stage.WAITING: "starting",
    Stage.DEPLOYING: "deploying",
    Stage.ROLLING_OUT: "starting",
    Stage.READY: "ready",
    Stage.DEGRADED: "degraded",
    Stage.FAILED: "failed",
}

# tmux style directives, and the reason they are named colours: a Linux VT has sixteen,
# and anything else is shoehorned into them by the console rather than by tmux -- the
# same lesson loom_usb_ingest.watch records at the top of its colour table.
TMUX_STYLE = {
    Stage.WAITING: "fg=colour250",
    Stage.DEPLOYING: "fg=yellow",
    Stage.ROLLING_OUT: "fg=yellow",
    Stage.READY: "fg=green",
    Stage.DEGRADED: "fg=red,bold",
    Stage.FAILED: "fg=red,bold",
}


def summary(readiness: Readiness | None) -> str:
    """The banner's one line, or nothing.

    Empty when there is nothing worth a row, and box.nix prints no line at all in that
    case -- a setup-mode box, the first seconds of a boot, and a box whose cluster has
    not answered yet all look exactly as they did before any of this existed.

    `WAITING` is deliberately among those. The pre-login banner is the one screen here
    with a hard height budget: it is written straight to the VT with no paging, so
    whatever does not fit scrolls off the top, taking the Loom mark with it -- and on a
    --wifi box it already carries a QR code. "waiting for the cluster" is what every boot
    says for its first minute, before anybody has walked up, and it is the one stage that
    tells a reader nothing they could act on. The line earns its row once there is a
    number on it, and a bring-up that fails still says so.

    The status line has no such budget and says `starting` throughout -- see `oneline`.
    """
    if readiness is None or readiness.stage is Stage.WAITING:
        return ""
    if readiness.stage is Stage.READY:
        return "Loom: ready."
    if readiness.stage is Stage.FAILED:
        return "Loom: failed to start. The console session has the log."
    return f"Loom: {STAGE_WORD[readiness.stage]} -- {_progress(readiness)}."


def oneline(readiness: Readiness | None) -> str:
    """The status line's segment, unstyled.

    Short: it shares a row with two controls.
    """
    if readiness is None:
        return ""
    if readiness.stage is Stage.READY:
        return "ready"
    if readiness.stage is Stage.FAILED:
        return "failed"
    if readiness.stage is Stage.WAITING:
        return "starting"
    return f"{STAGE_WORD[readiness.stage]} {readiness.counts.ready}/{readiness.counts.total}"


def tmux_oneline(readiness: Readiness | None) -> str:
    """`oneline`, wrapped in the style tmux will re-expand out of `#()` output."""
    if readiness is None:
        return ""
    text = oneline(readiness)
    if not text:
        return ""
    return f"#[{TMUX_STYLE[readiness.stage]}]{text}#[default]"


def stall_note(readiness: Readiness | None, now: float) -> str:
    """ "no change for 14m", or nothing.

    A count that is not moving is the failure a percentage hides most completely: nothing
    is crashing and nothing is pulling, the number simply stays where it is.
    """
    if readiness is None or readiness.stage in (Stage.READY, Stage.FAILED):
        return ""
    stalled = readiness.stalled_for(now)
    if stalled < STALL_AFTER_S:
        return ""
    return f"no change for {_minutes(stalled)}"


def _progress(readiness: Readiness) -> str:
    if readiness.counts.total <= 0:
        return "no workloads yet"
    return f"{readiness.counts.ready}/{readiness.counts.total} {UNIT} ready"


def _minutes(seconds: float) -> str:
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h{minutes % 60:02d}m"
