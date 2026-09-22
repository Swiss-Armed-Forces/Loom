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

The pinning is rich's `Live`. Anything printed through `live.console` lands *above* the
live renderable rather than overwriting it, so the journal keeps scrolling normally and
the panel stays on the last rows. That is why the journal is read line by line into this
process instead of being left to inherit the pane's stdout: a subprocess writing straight
to the terminal knows nothing about the rows Live has reserved, and would draw through it.

The handover condition is deliberately not evaluated here. It is `Readiness.settled`,
which is the publisher's `ROLLING_OUT`/`READY`/`DEGRADED` -- the same "unit is active and
the namespace exists" this pane used to test for itself, now stated once for the pane, the
status line and the banner alike.
"""

import logging
import os
import subprocess
import threading
import time
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


class Pane:
    """What runs in the pane.

    One object so the pieces can be exercised separately.
    """

    def __init__(
        self,
        settings: PaneSettings,
        console: Console | None = None,
        commands: Commands | None = None,
    ):
        self._unit = settings.unit
        self._state_dir = settings.state_dir
        self._k9s = settings.k9s
        self._setup_marker = settings.setup_marker
        self._console = console or Console()
        self._commands = commands or Commands()

    def run(self) -> int:
        self._preamble()
        journal = self._follow()

        if self._state_dir is None:
            # No publisher on this box -- setup mode, which has no cluster and never will
            # (ready.nix is run-mode only). The pane is the fetch log and nothing else,
            # so there is no panel to pin and nothing to hand over to.
            journal.wait()
            return 0

        readiness = self._watch(journal)
        _stop(journal)
        return self._handover(readiness)

    # ------------------------------------------------------------------------------
    # The log
    # ------------------------------------------------------------------------------
    def _preamble(self) -> None:
        self._console.print(
            f"  Following {self._unit}. This pane is the live bring-up log"
        )
        if self._k9s and self._state_dir is not None:
            self._console.print("  and becomes the pod list once Loom is up.")

        state = self._unit_state()
        if state == "inactive":
            # Setup mode guards loom-fetch with ConditionPathExists, so on every boot
            # after the first the unit never runs at all.
            if self._setup_marker and os.path.exists(self._setup_marker):
                self._console.print(
                    "  First-time setup already completed -- this mode powers the box\n"
                    '  off when it finishes. Boot the default "Loom" entry where the\n'
                    "  appliance is to be used. Below is the log of that run."
                )
            else:
                self._console.print(
                    f"  {self._unit} has not started yet;"
                    " output appears here when it does."
                )
        elif state == "failed":
            self._console.print(f"  {self._unit} FAILED. The end of its log is below.")
        self._console.print("")

    def _unit_state(self) -> str:
        completed = self._commands.run(
            ["systemctl", "show", "--property=ActiveState", "--value", self._unit]
        )
        return completed.stdout.strip() if completed.ok else "unknown"

    def _follow(self) -> subprocess.Popen:
        """Journalctl, read by this process rather than written straight to the pane.

        Deliberately not `--boot`: in setup mode the run worth reading is usually the
        previous boot's, because this boot skipped the unit on its marker.
        """
        # pylint: disable=consider-using-with
        # The handle outlives this call by design; `run` is what ends it.
        return subprocess.Popen(
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

    # ------------------------------------------------------------------------------
    # The panel
    # ------------------------------------------------------------------------------
    def _watch(self, journal: subprocess.Popen) -> Readiness | None:
        """Draw until the box is up, pumping the journal above the panel meanwhile."""
        readiness = read(self._state_dir or "")

        with Live(
            render.panel(readiness, time.time()),
            console=self._console,
            refresh_per_second=4,
            transient=False,
        ) as live:
            pump = threading.Thread(
                target=_pump, args=(journal, live), daemon=True, name="journal"
            )
            pump.start()

            while True:
                readiness = read(self._state_dir or "")
                live.update(render.panel(readiness, time.time()))
                if readiness is not None and readiness.settled and self._k9s:
                    return readiness
                time.sleep(REFRESH_INTERVAL_S)

    # ------------------------------------------------------------------------------
    # The handover
    # ------------------------------------------------------------------------------
    def _handover(self, readiness: Readiness | None) -> int:
        if not self._k9s:
            return 0

        # The panel's last word, on screen and still scrollable, because the pod list is
        # about to take the whole pane and everything printed here goes with it.
        self._console.print("")
        self._console.print(f"  {text.summary(readiness)}")
        self._console.print(
            "  This pane now shows the pods; the log is still there, on"
        )
        self._console.print(
            f"  an Alt-F2 console: journalctl --unit {self._unit} --follow"
        )
        self._console.print("")
        time.sleep(HANDOVER_GRACE_S)

        os.execv(self._k9s, [self._k9s])
        return 1  # unreachable; execv either replaces this process or raises


def _pump(journal: subprocess.Popen, live: Live) -> None:
    """Journal lines, printed above whatever Live has pinned to the bottom."""
    if journal.stdout is None:
        return
    for line in journal.stdout:
        # `markup=False`: a log line is not rich markup, and a container that logs
        # something in square brackets would otherwise be interpreted as a style and
        # vanish -- or raise, on the pane whose job is to show errors.
        live.console.print(line.rstrip("\n"), markup=False, highlight=False)


def _stop(journal: subprocess.Popen) -> None:
    journal.terminate()
    try:
        journal.wait(timeout=5)
    except subprocess.TimeoutExpired:
        journal.kill()
