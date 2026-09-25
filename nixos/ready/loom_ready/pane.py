"""The first pane of the operator's console session, in two halves of one life.

console.nix builds a three-pane session; this is what the widest of them runs. It was a
shell script there until the bar went in, and it does the same three things it always did:

  * Say where the unit stands before following it, because a bare `journalctl --follow` on
    a unit that has not started -- or that a condition skipped -- is an empty screen with
    no explanation.
  * Follow that unit's journal for the minutes or hours the box takes to come up.
  * Hand the pane over to k9s once up.sh has returned and the namespace exists, because by
    then the log is a finished transcript and the pods are the live thing.

What is new is the panel pinned along the bottom while all that scrolls past above it: how
many of the pods the cluster wants are ready, what is blocking, and how long it has been
since that moved. The log says what is happening; it has never said how much is left.

The pinning is rich's `Live`. Anything printed through the console `Live` was given lands
*above* the live renderable rather than overwriting it, so the journal keeps scrolling
normally and the panel stays on the last rows. That is why the journal is read line by
line into this process instead of being left to inherit the pane's stdout: a subprocess
writing straight to the terminal knows nothing about the rows Live has reserved, and would
draw through it.

Which makes the reading load-bearing rather than incidental, and that is the shape of
`Journal` below: the pipe has exactly one reader, `_drain`, and it is the thing that
prints. Both boot modes go through it. The first cut of this had the reader inside the
panel loop, which setup mode does not run -- so that pane opened a `journalctl` nobody
read, printed its two-line preamble and then showed an operator nothing at all for the
hours of a fetch, with the follower itself wedged once the pipe filled.

The handover condition is deliberately not evaluated here. It is `Readiness.settled`,
which is the publisher's `ROLLING_OUT`/`READY`/`DEGRADED` -- the same "unit is active and
the namespace exists" this pane used to test for itself, now stated once for the pane, the
status line and the banner alike. It costs one thing worth writing down: the handover now
depends on ready.nix's publisher still running, where the old shell asked systemd and
kubectl itself. A publisher that has died takes k9s with it (the unit is `Restart=always`,
so it has to die persistently), and what is left is the log -- which is the screen this
pane exists to show anyway.
"""

import logging
import os
import subprocess
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live

from loom_ready import render, text
from loom_ready.cluster import Commands
from loom_ready.state import Readiness, read

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_S = 1.0

# Long enough to read the two lines above the handover before k9s takes the screen: it
# draws on the alternate buffer, so everything printed here is gone until k9s exits.
HANDOVER_GRACE_S = 5.0

JOURNAL_LINES = "500"

# How long to wait for journalctl to go away once it has been asked to.
JOURNAL_STOP_S = 5.0


@dataclass(frozen=True)
class PaneSettings:
    """What console.nix's wrapper baked into this pane.

    Kept together rather than passed one by one because they are one fact: which of the
    two boot modes this pane is running in. Run mode has a publisher, a cluster and
    somewhere to hand over to; setup mode has a fetch log, a marker file saying whether
    that fetch already happened, and no cluster coming.
    """

    unit: str
    # Empty means no publisher -- see the note in `Pane.run`.
    state_dir: str | None = None
    k9s: str | None = None
    setup_marker: str | None = None


@dataclass(frozen=True)
class PaneTiming:
    """The two waits in here, injected the way the console and the journal are.

    Both are behaviour rather than scaffolding -- how often the panel redraws, and how
    long the handover leaves its last lines on a screen somebody is reading -- but a
    suite that took the defaults would spend six seconds per case watching a clock.
    """

    refresh: float = REFRESH_INTERVAL_S
    handover_grace: float = HANDOVER_GRACE_S


class Journal:
    """A unit's journal, as lines, for as long as the pane wants them.

    A class rather than a bare `Popen` for two reasons. It keeps the pipe and the thing
    that reads it in one place, which is the invariant the pane depends on; and it is
    the pane's one seam onto systemd, so tests/test_pane.py can hand `Pane` a journal of
    canned lines rather than patching a subprocess into place.
    """

    def __init__(self, unit: str):
        self._unit = unit
        self._process: subprocess.Popen | None = None

    def lines(self) -> Iterator[str]:
        """Every line, until journalctl ends -- which under `--follow` means `stop`.

        Deliberately not `--boot`: in setup mode the run worth reading is usually the
        previous boot's, because this boot skipped the unit on its marker.
        """
        # pylint: disable=consider-using-with
        # The process outlives this call by design; `stop` is what ends it.
        self._process = subprocess.Popen(
            [
                "journalctl",
                "--no-hostname",
                f"--lines={JOURNAL_LINES}",
                "--follow",
                "--unit",
                self._unit,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if self._process.stdout is None:
            return
        for line in self._process.stdout:
            yield line.rstrip("\n")

    def stop(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=JOURNAL_STOP_S)
        except subprocess.TimeoutExpired:
            process.kill()


class Pane:
    """What runs in the pane.

    One object so the pieces can be exercised separately.
    """

    def __init__(
        self,
        settings: PaneSettings,
        console: Console | None = None,
        commands: Commands | None = None,
        journal: Journal | None = None,
        timing: PaneTiming | None = None,
    ):
        # Held whole rather than unpacked: the four fields are one fact -- which boot
        # mode this pane is in -- and every reader below asks the same question of them.
        self._settings = settings
        self._console = console or Console()
        self._commands = commands or Commands()
        self._journal = journal or Journal(settings.unit)
        self._timing = timing or PaneTiming()

    def run(self) -> int:
        self._preamble()

        if self._settings.state_dir is None:
            # No publisher on this box -- setup mode, which has no cluster and never will
            # (ready.nix is run-mode only), or a run-mode box told to stop publishing.
            # The pane is the log and nothing else: no panel to pin, and nothing to hand
            # over to. The lines still have to be read *here*, because this process is
            # the only reader the pipe has.
            self._drain()
            return 0

        readiness = self._watch()
        self._journal.stop()
        return self._handover(readiness)

    # ------------------------------------------------------------------------------
    # The log
    # ------------------------------------------------------------------------------
    def _preamble(self) -> None:
        self._console.print(
            f"  Following {self._settings.unit}. This pane is the live bring-up log"
        )
        if self._settings.k9s and self._settings.state_dir is not None:
            self._console.print("  and becomes the pod list once Loom is up.")

        state = self._unit_state()
        if state == "inactive":
            self._console.print(self._inactive_note())
        elif state == "failed":
            self._console.print(
                f"  {self._settings.unit} FAILED. The end of its log is below."
            )
        self._console.print("")

    def _inactive_note(self) -> str:
        """Why there is nothing on screen yet, which is a different why per mode.

        The marker is only setup mode's to read, and "no publisher" is how this pane
        knows it is in setup mode. Run mode's filesystem carries the same file -- the
        setup specialisation that wrote it installed this very box -- so a run-mode pane
        that consulted it would tell an operator their box powers itself off when it is
        finished, which is setup mode's behaviour and emphatically not this one's.
        """
        if (
            self._settings.state_dir is None
            and self._settings.setup_marker
            and os.path.exists(self._settings.setup_marker)
        ):
            # Setup mode guards loom-fetch with ConditionPathExists, so on every boot
            # after the first the unit never runs at all.
            return (
                "  First-time setup already completed -- this mode powers the box\n"
                '  off when it finishes. Boot the default "Loom" entry where the\n'
                "  appliance is to be used. Below is the log of that run."
            )
        return f"  {self._settings.unit} has not started yet; output appears here when it does."

    def _unit_state(self) -> str:
        completed = self._commands.run(
            [
                "systemctl",
                "show",
                "--property=ActiveState",
                "--value",
                self._settings.unit,
            ]
        )
        return completed.stdout.strip() if completed.ok else "unknown"

    def _drain(self) -> None:
        """The journal, printed through the console rather than around it.

        While `Live` is running this is the console it was given, so every line lands
        above the pinned panel; with no panel it is the pane's own output. One reader
        either way.
        """
        for line in self._journal.lines():
            # `markup=False`: a log line is not rich markup, and up.sh's own `[*]` prefix
            # -- or a container that logs something in square brackets -- would otherwise
            # be interpreted as a style and vanish, or raise, on the pane whose job is to
            # show errors.
            self._console.print(line, markup=False, highlight=False)

    # ------------------------------------------------------------------------------
    # The panel
    # ------------------------------------------------------------------------------
    def _watch(self) -> Readiness | None:
        """Draw until the box is up, pumping the journal above the panel meanwhile."""
        readiness = read(self._settings.state_dir or "")

        with Live(
            render.panel(readiness, time.time()),
            console=self._console,
            refresh_per_second=4,
            transient=False,
        ) as live:
            # The pump is handed no `live`: starting one hooks the console it was given,
            # which is this one, and that hook is what puts a printed line above the
            # panel rather than through it.
            pump = threading.Thread(target=self._drain, daemon=True, name="journal")
            pump.start()

            while True:
                readiness = self._panel_turn(live)
                if readiness is not None:
                    return readiness
                time.sleep(self._timing.refresh)

    def _panel_turn(self, live: Live) -> Readiness | None:
        """One turn of the panel loop: re-read, redraw, and decide whether to stop.

        A method rather than the body of the loop above so that the turn is a thing a
        test can count -- the case that matters is a *failed* bring-up, where what has
        to be shown is that the loop went round again instead of handing over, and there
        is nothing on a non-terminal console to observe that by. See tests/doubles.py's
        RecordingPane.
        """
        readiness = read(self._settings.state_dir or "")
        live.update(render.panel(readiness, time.time()))
        if readiness is not None and readiness.settled and self._settings.k9s:
            return readiness
        return None

    # ------------------------------------------------------------------------------
    # The handover
    # ------------------------------------------------------------------------------
    def _handover(self, readiness: Readiness | None) -> int:
        if not self._settings.k9s:
            return 0

        # The panel's last word, on screen and still scrollable, because the pod list is
        # about to take the whole pane and everything printed here goes with it.
        self._console.print("")
        self._console.print(f"  {text.summary(readiness)}")
        self._console.print(
            "  This pane now shows the pods; the log is still there, on"
        )
        self._console.print(
            f"  an Alt-F2 console: journalctl --unit {self._settings.unit} --follow"
        )
        self._console.print("")
        time.sleep(self._timing.handover_grace)

        return self._become(self._settings.k9s)

    def _become(self, program: str) -> int:
        """Replace this process with k9s.

        Its own method because it is the one thing in here that cannot be undone, and
        tests/test_pane.py overrides it to record the handover rather than to perform
        it.
        """
        os.execv(program, [program])
        return 1  # unreachable; execv either replaces this process or raises
