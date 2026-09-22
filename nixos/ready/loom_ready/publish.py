"""The one process that works the answer out.

Runs as root out of `loom-ready.service` (ready.nix) with the operator's kubeconfig,
polls the cluster, and writes `state.json` and `summary` where the three readers find
them. One publisher rather than three, because the readers are a tmux status line
refreshing every five seconds, a pane, and a banner generator that can start at any
moment -- three independent pollers would triple the load on an API server during the
exact window the box is at its busiest, and the status line has to be a file read rather
than a `kubectl` invocation or it would stall the whole tmux server on a cluster that is
not answering.

The one thing this does beyond publishing is the banner. box.nix's `loom-info` renders
the pre-login screen once per boot into /run/issue.d, so a box that came up an hour ago
would otherwise still be telling whoever walks past that it is starting. On a *stage*
change -- never on a count change, which would repaint several times a minute -- this
runs the command it was given, which on the appliance is `loom-banner-refresh`: rewrite
the issue, and restart tty1's getty if and only if nobody has pressed a key yet. Same
mechanism key-guard.nix uses to keep its own line honest.
"""

import logging
import time
from dataclasses import dataclass, field

from loom_ready.cluster import Cluster, Commands, classify, tally
from loom_ready.state import Counts, Readiness, Stage, publish
from loom_ready.text import summary

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_S = 5.0


@dataclass(frozen=True)
class PublishSettings:
    """What ready.nix's unit baked into the publisher."""

    state_dir: str
    interval: float = DEFAULT_INTERVAL_S
    # The banner refresh, as argv. Empty is a publisher nobody asked to redraw anything,
    # which is what the tests and a hand-run debugging copy want.
    on_change: list[str] = field(default_factory=list)


class Publisher:
    """Poll, decide, publish.

    Holds the only state a tick cannot derive for itself.
    """

    def __init__(
        self,
        cluster: Cluster,
        settings: PublishSettings,
        commands: Commands | None = None,
    ):
        self._cluster = cluster
        self._settings = settings
        self._commands = commands or Commands()
        self._stage: Stage | None = None
        self._counts = Counts()
        self._changed = 0.0

    def tick(self, now: float | None = None) -> Readiness:
        """One observation, published.

        Returns what it wrote, for the tests.
        """
        now = time.time() if now is None else now

        observation = self._cluster.observe()
        stage = classify(observation, self._stage)
        counts = tally(observation.workloads)

        # When the numbers last moved, not when this record was written. A box pulling a
        # multi-gigabyte image and a box whose scheduler has nowhere to put the next pod
        # look identical in a percentage; they differ in how long it has been since this
        # changed.
        if counts != self._counts or not self._changed:
            self._changed = now
        self._counts = counts

        readiness = Readiness(
            stage=stage,
            counts=counts,
            workloads=observation.workloads,
            blockers=observation.blockers,
            detail=observation.detail,
            updated=now,
            changed=self._changed,
        )
        publish(self._settings.state_dir, readiness, summary(readiness))

        if stage is not self._stage:
            previous, self._stage = self._stage, stage
            logger.info("readiness: %s -> %s", previous or "start", stage)
            # Every change but the first one. At boot the banner is being redrawn anyway
            # -- box.nix's loom-banner-repaint watches the console for a minute while the
            # font and the DRM driver resize it, and picks up whatever this has written by
            # then -- so a refresh here would be a second, uncoordinated getty restart
            # inside that same window. That matters: a getty restart eats the keypress
            # that opens the operator's session, and the first tick lands within seconds
            # of the login prompt appearing.
            if previous is not None:
                self._refresh_banner()

        return readiness

    def run(self) -> int:
        """Forever.

        The unit is what stops it.
        """
        while True:
            self.tick()
            time.sleep(self._settings.interval)

    def _refresh_banner(self) -> None:
        if not self._settings.on_change:
            return
        completed = self._commands.run(self._settings.on_change)
        if not completed.ok:
            # Best effort, always. The banner is a display, and a box whose login screen
            # is one stage out of date is still a box that is coming up.
            logger.warning("Banner refresh failed: %s", completed.stderr)
