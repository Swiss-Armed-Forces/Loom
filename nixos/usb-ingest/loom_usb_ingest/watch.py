"""Drawing the copy, in the pane `pane.py` split off the console session.

Started by the ingest, as the command of the new pane, and it runs as the operator
rather than as root -- the tmux server spawns it. All it may do, therefore, is read the
world-readable records under the progress directory and draw them.

It ends itself when the last record is gone, which is what reverts the split: a pane
whose command exits is closed by tmux, so "the operator unplugged the last stick" and
"k9s gets its space back" are the same event rather than two that have to be kept in
step.

A record is gone when the ingest withdrew it OR when the device it describes is no
longer there -- the second is a backstop for the first, and the reason the pane cannot
be left split across a missed udev event. Note that neither of those is "the copy
finished": that is the moment this pane exists to show, and it is the one moment it must
not disappear at. See `release` in __main__.py.
"""

import time

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from loom_usb_ingest.progress import DeviceProgress, Stage, device_present, read_all

REFRESH_INTERVAL_S = 1.0

# How long the pane stays after the last device is gone. By then the stick is out of
# the operator's hand, so this is not reading time -- it is slack, so that a record
# withdrawn a moment before the pane is killed from outside does not leave a flash of
# an empty pane behind.
LINGER_S = 3.0

GIBIBYTE = 1024**3

# Named colours rather than rich's defaults, which are 24-bit and land somewhere
# unreadable once a Linux VT has shoehorned them into its sixteen.
BAR_BACK = "bright_black"


STAGE_STYLE = {
    Stage.WAITING: "yellow",
    Stage.COPYING: "bold yellow",
    Stage.DONE: "bold green",
    Stage.FAILED: "bold red",
    Stage.INTERRUPTED: "bold red",
}


def render(records: list[DeviceProgress]) -> RenderableType:
    """The whole pane: one row per device, plus what to do about it."""
    if not records:
        return Text("No USB media being ingested.", style="dim")

    table = Table.grid(padding=(0, 1))
    table.add_column(no_wrap=True)  # device and name
    table.add_column(width=20)  # the bar
    table.add_column(no_wrap=True)  # bytes and objects
    table.add_column(overflow="fold")  # what it is doing

    for record in records:
        table.add_row(
            Text(f"{record.device} {record.name}", style="bold"),
            _bar(record),
            Text(_counts(record), style="dim"),
            _status(record),
        )

    hint = Text()
    if any(record.finished for record in records):
        hint = Text(
            "Finished sticks can be unplugged; this pane closes when the last one"
            " is out.",
            style="dim",
        )
    elif any(record.stage is Stage.COPYING for record in records):
        hint = Text(
            "Leave the stick in until its row says so.",
            style="dim",
        )

    return Group(table, hint)


def _bar(record: DeviceProgress) -> ProgressBar:
    """A bar when the volume's size is known, a pulse when it is not.

    `total=None` is rich's own pulse, which is the honest rendering of a filesystem that
    would not say how much is on it -- see `progress.volume_bytes`.
    """
    if record.finished:
        colour = "green" if record.stage is Stage.DONE else "red"
        return ProgressBar(
            total=1,
            completed=1,
            style=BAR_BACK,
            complete_style=colour,
            finished_style=colour,
        )
    if not record.counts.total:
        return ProgressBar(total=None, pulse=True, style=BAR_BACK, pulse_style="yellow")
    return ProgressBar(
        total=record.counts.total,
        completed=min(record.counts.copied, record.counts.total),
        style=BAR_BACK,
        complete_style="yellow",
        finished_style="green",
    )


def _counts(record: DeviceProgress) -> str:
    # A finished device is reported as one figure rather than as a fraction: what
    # `finish` leaves behind is the whole device's total, so "12.3/12.3 GiB" would be
    # the same number written twice -- and `total` is per volume in any case.
    if record.counts.total and not record.finished:
        return (
            f"{record.counts.copied / GIBIBYTE:5.1f}/{record.counts.total / GIBIBYTE:.1f} GiB"
            f"  {record.counts.objects} files"
        )
    return f"{record.counts.copied / GIBIBYTE:5.1f} GiB  {record.counts.objects} files"


def _status(record: DeviceProgress) -> Text:
    style = STAGE_STYLE[record.stage]
    if record.stage is Stage.WAITING:
        return Text("waiting for Loom to answer", style=style)
    if record.stage is Stage.COPYING:
        where = ""
        if record.volume.count > 1:
            where = f" ({record.volume.index}/{record.volume.count})"
        return Text(f"copying {record.volume.path}{where}", style=style)
    if record.stage is Stage.FAILED:
        # The reason, when the ingest had one. This column folds rather than
        # truncating, so a long one costs the row a second line and nothing else --
        # and an operator who can see "connection refused" can do something about it,
        # where "1 failed" only tells them to find somebody who can read a journal.
        reason = f": {record.message}" if record.message else ""
        return Text(
            f"{record.counts.failures} failed{reason} -- safe to remove", style=style
        )
    if record.stage is Stage.INTERRUPTED:
        return Text("stopped before it finished -- safe to remove", style=style)
    # A finished stick can still have something to say: a volume that was skipped
    # costs the operator documents they expected to see, without costing the copy a
    # failure.
    if record.message:
        return Text(f"DONE ({record.message}) -- safe to remove", style=style)
    return Text("DONE -- safe to remove", style=style)


def watch(progress_dir: str, console: Console | None = None) -> int:
    """Draw until there is nothing left to draw."""
    console = console or Console()
    empty_since: float | None = None

    with Live(console=console, refresh_per_second=4, transient=False) as live:
        while True:
            records = [
                record for record in read_all(progress_dir) if device_present(record)
            ]
            live.update(render(records))

            if records:
                empty_since = None
            else:
                empty_since = empty_since or time.monotonic()
                if time.monotonic() - empty_since >= LINGER_S:
                    return 0

            time.sleep(REFRESH_INTERVAL_S)
