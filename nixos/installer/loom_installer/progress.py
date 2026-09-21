"""A progress display for the one step that takes long enough to need one.

Copying the appliance closure onto the internal disk is tens of gigabytes, and it
is the part of an install an operator is standing there watching. Everything else
the installer does is seconds.

Two things had to stay true of it:

  * The copy's own output still reaches the screen. It is printed *above* the bar
    rather than swallowed, because a failed install with no visible reason is the
    worst thing that can happen on media whose whole job is being diagnosable by
    whoever is standing at the box.
  * It degrades to a spinner rather than lying. `nixos-install` reports paths, not
    bytes, and how many are left is not knowable from outside it -- so the bar is
    driven by how full the target filesystem is, and when the closure's size could
    not be established there is nothing to be a fraction of.

The same display, with the same two properties, is what the appliance's USB ingest
draws into its console pane (nixos/usb-ingest); this one is the installer's copy of
the idea, not a shared module, because the two run on different systems and neither
image carries the other's code.
"""

import os
import threading
import types
from typing import Self

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from loom_installer.console import Ui

# How often the filesystem is re-measured. `nixos-install` can be quiet for a while
# on a large path, and a bar that only moves when a line arrives looks stuck.
POLL_INTERVAL_S = 1.0

GIBIBYTE = 1024**3


class CopyProgress:
    """A bar over a filesystem filling up, with a log scrolling above it."""

    def __init__(self, ui: Ui, mountpoint: str, total_bytes: int | None) -> None:
        self._mountpoint = mountpoint
        self._total = total_bytes
        self._baseline = _used_bytes(mountpoint)
        self._stop = threading.Event()
        self._poller: threading.Thread | None = None

        # `line` rather than rich's default: the VT font carries about 515 glyphs and
        # braille is not among them. See console.py.
        columns: list[TextColumn | BarColumn | SpinnerColumn | TimeElapsedColumn] = [
            SpinnerColumn(spinner_name="line", style="loom.brand"),
            TextColumn("[loom.quiet]{task.description}"),
        ]
        if total_bytes is not None:
            columns += [
                BarColumn(
                    # Named colours rather than rich's 24-bit defaults, which a
                    # Linux VT shoehorns into somewhere unreadable.
                    style="bright_black",
                    complete_style="loom.brand",
                    finished_style="loom.ok",
                ),
                TaskProgressColumn(),
                TextColumn("[loom.quiet]{task.fields[copied]}"),
            ]
        columns.append(TimeElapsedColumn())

        self._progress = Progress(
            *columns,
            console=ui.out,
            # Left on screen: the finished bar is the receipt for the longest step
            # of the install, directly above the recovery passphrase.
            transient=False,
            # A console that is not a terminal gets one line per refresh otherwise.
            disable=not ui.interactive,
        )
        self._task = self._progress.add_task(
            "Copying the appliance closure",
            total=total_bytes,
            copied=_gib(0, total_bytes),
        )

    def __enter__(self) -> Self:
        self._progress.start()
        self._poller = threading.Thread(target=self._poll, daemon=True)
        self._poller.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self._stop.set()
        if self._poller is not None:
            self._poller.join(timeout=POLL_INTERVAL_S * 2)
        if exc is None and self._total is not None:
            # The bar ends full. The measurement is the filesystem's, which includes
            # neither the metadata ext4 keeps for itself nor the rounding every file
            # costs, so it never quite reaches the NAR total on its own.
            self._progress.update(self._task, completed=self._total)
        self._progress.stop()

    def log(self, line: str) -> None:
        """One line of the copy's own output, above the bar."""
        if line:
            self._progress.console.print(line, style="loom.quiet", highlight=False)

    def _poll(self) -> None:
        while not self._stop.wait(POLL_INTERVAL_S):
            self._advance()

    def _advance(self) -> None:
        copied = max(0, _used_bytes(self._mountpoint) - self._baseline)
        if self._total is None:
            self._progress.update(self._task, copied=_gib(copied, None))
            return
        self._progress.update(
            self._task,
            completed=min(copied, self._total),
            copied=_gib(copied, self._total),
        )


def _used_bytes(mountpoint: str) -> int:
    try:
        stats = os.statvfs(mountpoint)
    except OSError:
        return 0
    return (stats.f_blocks - stats.f_bfree) * stats.f_frsize


def _gib(copied: int, total: int | None) -> str:
    if total is None:
        return f"{copied / GIBIBYTE:.1f} GiB"
    return f"{copied / GIBIBYTE:.1f}/{total / GIBIBYTE:.1f} GiB"
