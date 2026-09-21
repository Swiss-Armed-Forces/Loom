"""What the box has decided about its own readiness, and where it says so.

One process works the answer out -- `publish.py`, out of a root unit with the operator's
kubeconfig -- and three readers draw it: the bring-up pane, the tmux status line and the
pre-login banner. They share a directory and nothing else, the same arrangement
`loom_usb_ingest.progress` uses and for the same reason: the readers run as the operator
(the tmux server spawns two of them) while the writer needs the cluster, and a file is the
whole of what they have in common.

Two files rather than one, and the second is not a duplicate:

  * `state.json`  Everything, for the pane and the status line. Both already have a Python
                  interpreter in hand.
  * `summary`     One line of plain text, for box.nix's `loom-info`. That is a shell
                  script assembling an agetty issue file, and giving it a JSON document to
                  parse would mean putting `jq` in the banner's closure to render a line it
                  could have been handed. It reads the key guard's state the same way.

The `summary` line is ASCII with no backslash in it, which is not a style preference:
agetty reads a backslash in an issue file as the start of an escape of its own and eats it
before anyone sees it (box.nix:84-88). `text.summary` is what guarantees that, and
tests/test_text.py is what keeps it true.
"""

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)

STATE_NAME = "state.json"
SUMMARY_NAME = "summary"

# How old a published record may be before a reader stops believing it. Three polls: one
# missed tick is a slow `kubectl`, three in a row means the publisher is gone -- the unit
# died, or this is a setup-mode box that never had one. A stale record is worse than none,
# because "ready" that stopped being recomputed an hour ago is exactly the claim an
# operator would act on.
STALE_AFTER_S = 45.0


class Stage(StrEnum):
    """How far the bring-up has got.

    Ordered by the sequence a healthy boot walks through, which is also the order the
    console treats them in -- `ROLLING_OUT` and later mean up.sh has returned.
    """

    WAITING = "waiting"
    DEPLOYING = "deploying"
    ROLLING_OUT = "rolling-out"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"


# The stages in which up.sh has returned and the namespace exists -- which is, to the
# letter, the condition console.nix's pane used to evaluate for itself before handing the
# screen over to k9s. Keeping it as a set here rather than as a comparison means the pane
# and the publisher cannot drift about what "up" means.
SETTLED_STAGES = frozenset({Stage.ROLLING_OUT, Stage.READY, Stage.DEGRADED})


@dataclass(frozen=True)
class Workload:
    """One Deployment, StatefulSet, DaemonSet or Job, reduced to two numbers.

    `desired` of 0 is a workload nobody is waiting for: a KEDA-idle Deployment in its
    healthy steady state. `counted` is what keeps those out of the denominator -- see
    cluster.py.
    """

    kind: str
    name: str
    desired: int
    ready: int

    @property
    def counted(self) -> bool:
        return self.desired > 0

    @property
    def converged(self) -> bool:
        return self.ready >= self.desired


@dataclass(frozen=True)
class Blocker:
    """A pod that is not going to become ready on its own, and why."""

    pod: str
    reason: str


@dataclass(frozen=True)
class Counts:
    """Replicas ready out of replicas wanted, over the workloads that are counted."""

    ready: int = 0
    total: int = 0

    @property
    def fraction(self) -> float:
        """0.0 when nothing is known yet, which the renderers draw as a pulse."""
        if self.total <= 0:
            return 0.0
        return min(self.ready / self.total, 1.0)


@dataclass(frozen=True)
class Readiness:
    """The whole answer, as published.

    `changed` is when `counts` last moved, not when this record was written: it is what
    lets a renderer say "no change for 14m", which on a box pulling a multi-gigabyte image
    is the difference between slow and stuck.
    """

    stage: Stage = Stage.WAITING
    counts: Counts = field(default_factory=Counts)
    workloads: list[Workload] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    # Free text from whatever could not be reached, shown while waiting. kubectl's own
    # message, so "no cluster", "no namespace" and "certificate expired" do not all
    # arrive as the same silence.
    detail: str = ""
    updated: float = 0.0
    changed: float = 0.0

    @property
    def settled(self) -> bool:
        """True once up.sh has returned and the namespace exists."""
        return self.stage in SETTLED_STAGES

    def stalled_for(self, now: float) -> float:
        """Seconds since the ready count last moved. 0 when it never has."""
        if not self.changed:
            return 0.0
        return max(now - self.changed, 0.0)


def state_path(state_dir: str) -> str:
    return os.path.join(state_dir, STATE_NAME)


def summary_path(state_dir: str) -> str:
    return os.path.join(state_dir, SUMMARY_NAME)


def publish(state_dir: str, readiness: Readiness, summary: str) -> None:
    """Write both files, atomically.

    Through a temporary file in the same directory, so a reader can never catch a
    half-written document. The status line reads this every five seconds and the banner
    generator reads it from a unit that can start at any moment; neither may see half a
    number. Same mechanism as `loom_usb_ingest.progress.publish` and key-guard.nix's
    `put`.
    """
    try:
        os.makedirs(state_dir, mode=0o755, exist_ok=True)
        _replace(state_path(state_dir), json.dumps(asdict(readiness)), state_dir)
        _replace(summary_path(state_dir), summary + "\n", state_dir)
    except OSError as error:
        # Never fatal. This is a display, and a box that cannot draw its own progress is
        # still a box that is coming up.
        logger.warning("Could not publish readiness: %s", error)


def _replace(path: str, content: str, state_dir: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", dir=state_dir, delete=False, encoding="utf-8"
    ) as handle:
        handle.write(content)
        temporary = handle.name
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def read(state_dir: str, now: float | None = None) -> Readiness | None:
    """The published record, or None if there is not a usable one.

    None covers every way this can fail, and the readers all treat it the same way: draw
    nothing. A status line that says nothing looks exactly like the one this box shipped
    with before any of this existed, which is the right thing for a setup-mode box, for
    the first seconds of a boot, and for a publisher that has died.
    """
    try:
        with open(state_path(state_dir), encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError):
        return None

    record = _parse(raw)
    if record is None:
        return None

    now = time.time() if now is None else now
    if now - record.updated > STALE_AFTER_S:
        return None
    return record


def _parse(raw: object) -> Readiness | None:
    if not isinstance(raw, dict):
        return None
    try:
        return Readiness(
            stage=Stage(raw["stage"]),
            counts=Counts(
                ready=int(raw["counts"]["ready"]),
                total=int(raw["counts"]["total"]),
            ),
            workloads=[
                Workload(
                    kind=str(item["kind"]),
                    name=str(item["name"]),
                    desired=int(item["desired"]),
                    ready=int(item["ready"]),
                )
                for item in raw["workloads"]
            ],
            blockers=[
                Blocker(pod=str(item["pod"]), reason=str(item["reason"]))
                for item in raw["blockers"]
            ],
            detail=str(raw["detail"]),
            updated=float(raw["updated"]),
            changed=float(raw["changed"]),
        )
    except (KeyError, TypeError, ValueError):
        # A record written by a different version of this program. Dropping it costs one
        # refresh; refusing to read any would cost the display.
        return None
