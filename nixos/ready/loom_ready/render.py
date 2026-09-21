"""Drawing readiness, for the two places that have a terminal.

The bring-up pane and the one-shot `loom-ready` share every line of this, which is the
point: an operator who types the command on an Alt-F2 console should not have to map what
they see onto what the pane was showing.

Two rules come from the screen this lands on. Both are the same rules
`loom_usb_ingest.watch` records:

  * Named colours only. rich's defaults are 24-bit, and a Linux VT shoehorns those into
    its sixteen on its own -- landing, more often than not, somewhere unreadable.
  * A bar only when the total is known. `total=None` is rich's pulse, and it is the honest
    rendering of a cluster that has not said how many replicas it wants yet.

The bar glyphs are rich's own -- U+2501 and the two half-blocks -- and branding.nix
asserts the console font carries them, alongside the three the Loom mark is drawn from.
A missing glyph is a hole on a screen nobody sees until the box is at a site.
"""

from rich.console import Group, RenderableType
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from loom_ready import text
from loom_ready.state import Readiness, Stage

BAR_WIDTH = 24
BAR_BACK = "bright_black"

STAGE_STYLE = {
    Stage.WAITING: "dim",
    Stage.DEPLOYING: "bold yellow",
    Stage.ROLLING_OUT: "bold yellow",
    Stage.READY: "bold green",
    Stage.DEGRADED: "bold red",
    Stage.FAILED: "bold red",
}

BAR_COLOUR = {
    Stage.WAITING: "yellow",
    Stage.DEPLOYING: "yellow",
    Stage.ROLLING_OUT: "yellow",
    Stage.READY: "green",
    Stage.DEGRADED: "red",
    Stage.FAILED: "red",
}

STAGE_NOTE = {
    Stage.WAITING: "waiting for the cluster",
    Stage.DEPLOYING: "deploying",
    Stage.ROLLING_OUT: "rolling out",
    Stage.READY: "ready -- browse https://frontend.loom",
    Stage.DEGRADED: "was ready, now degraded",
    Stage.FAILED: "bring-up failed",
}


def panel(readiness: Readiness | None, now: float) -> RenderableType:
    """The two or three lines the pane keeps pinned below the log."""
    if readiness is None:
        # Not an error and not a blank: on a setup-mode box there is no cluster coming,
        # and the operator is looking at a fetch log that says so itself.
        return Text("Readiness is not being published on this box.", style="dim")

    row = Table.grid(padding=(0, 1))
    row.add_column(no_wrap=True)
    row.add_column(width=BAR_WIDTH)
    row.add_column(no_wrap=True)
    row.add_column(overflow="fold")
    row.add_row(
        Text("Loom", style="bold"),
        _bar(readiness),
        Text(_counts(readiness), style="dim"),
        Text(STAGE_NOTE[readiness.stage], style=STAGE_STYLE[readiness.stage]),
    )

    lines: list[RenderableType] = [row]
    note = _note(readiness, now)
    if note is not None:
        lines.append(note)
    return Group(*lines)


def report(readiness: Readiness | None, now: float) -> RenderableType:
    """What `loom-ready` prints when it is typed at a prompt.

    The panel, plus the workloads that are still outstanding -- which is the question
    somebody types the command to answer, and the one k9s makes them read 25 rows for.
    """
    if readiness is None:
        return Text("Readiness is not being published on this box.", style="dim")

    outstanding = [
        workload
        for workload in readiness.workloads
        if workload.counted and not workload.converged
    ]
    if not outstanding:
        return panel(readiness, now)

    table = Table.grid(padding=(0, 2))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True)
    for workload in sorted(outstanding, key=lambda item: item.name):
        table.add_row(
            Text(workload.name),
            Text(workload.kind, style="dim"),
            Text(f"{workload.ready}/{workload.desired}", style="yellow"),
        )
    return Group(panel(readiness, now), Text(""), table)


def _bar(readiness: Readiness) -> ProgressBar:
    colour = BAR_COLOUR[readiness.stage]
    if readiness.counts.total <= 0:
        return ProgressBar(
            total=None, pulse=True, width=BAR_WIDTH, style=BAR_BACK, pulse_style=colour
        )
    return ProgressBar(
        total=readiness.counts.total,
        completed=min(readiness.counts.ready, readiness.counts.total),
        width=BAR_WIDTH,
        style=BAR_BACK,
        complete_style=colour,
        finished_style=colour,
    )


def _counts(readiness: Readiness) -> str:
    if readiness.counts.total <= 0:
        return f"--/-- {text.UNIT}"
    return f"{readiness.counts.ready}/{readiness.counts.total} {text.UNIT}"


def _note(readiness: Readiness, now: float) -> Text | None:
    """The second line: why it is not moving, or what could not be reached."""
    if readiness.blockers:
        listed = ", ".join(
            f"{blocker.pod} ({blocker.reason})" for blocker in readiness.blockers
        )
        return Text(f"  waiting on: {listed}", style="red")

    stalled = text.stall_note(readiness, now)
    if stalled:
        return Text(f"  {stalled}", style="yellow")

    if readiness.stage is Stage.WAITING and readiness.detail:
        return Text(f"  {readiness.detail}", style="dim")
    return None
