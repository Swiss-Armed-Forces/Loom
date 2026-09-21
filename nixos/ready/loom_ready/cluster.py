"""Asking the cluster how far along it is, and deciding what the answer means.

Split deliberately down the middle: everything that shells out is in `Commands` and
`Cluster`, and everything that decides is a plain function over parsed JSON. The rules
below are the whole point of this package and none of them needs a cluster to exercise --
see tests/test_cluster.py, which feeds them the documents a real bring-up produces.

Workloads, not pods. A pod list cannot express "desired": a Deployment rolling out has no
pods for the replicas it has not created yet, so counting pods makes the denominator
follow the numerator and the bar sits near the end from the first second. The workload
objects carry both numbers.

                        desired                            ready
  Deployment            .spec.replicas (default 1)         .status.readyReplicas
  StatefulSet           .spec.replicas (default 1)         .status.readyReplicas
  DaemonSet             .status.desiredNumberScheduled     .status.numberReady
  Job                   .spec.completions (default 1)      .status.succeeded

A workload with `desired == 0` is dropped rather than counted as incomplete. That is a
KEDA-idle Deployment -- charts/templates/{worker,tika,gotenberg,ollama}/*scaledobjects.yaml
scale from `minReplicas`, which is allowed to be zero -- and it is the healthy steady
state, not something to wait for. Counting those would park the bar short of the end for
the life of the box.

Jobs are counted because they gate: charts/templates/common/init-{elasticsearch,s3}-job.yaml
and the three under pre-install/ have to finish before anything that depends on them
works, and they reach `Succeeded` rather than `Ready` -- so a readiness check written in
terms of Ready pods alone never sees them at all. A Job that has been garbage-collected is
simply absent, which is correctly read as "not blocking".
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field

from loom_ready.state import Blocker, Counts, Stage, Workload

logger = logging.getLogger(__name__)

# Every kubectl call carries this. The interesting failure is not a missing kubeconfig --
# that returns at once -- but a kubeconfig pointing at a minikube that is not running,
# where the default is a two-minute hang per attempt. A poll loop built out of those stops
# being a poll loop. The same trap is documented in console.nix's loom-k9s.
REQUEST_TIMEOUT = "5s"

# Kill the process a little after kubectl should have given up on its own, so a client
# that hangs below its own timeout cannot wedge the loop either.
SUBPROCESS_TIMEOUT_S = 15.0

WORKLOAD_KINDS = "deployments,statefulsets,daemonsets,jobs"

# Container states that will not resolve by waiting. Naming one of these on the console is
# worth more than any percentage: it is the difference between "this box is slow" and
# "this box needs somebody".
FATAL_WAITING_REASONS = frozenset(
    {
        "ImagePullBackOff",
        "ErrImagePull",
        "CrashLoopBackOff",
        "CreateContainerConfigError",
        "CreateContainerError",
        "InvalidImageName",
    }
)

# How many to carry. The pane has a few lines, not a screen, and a cluster where twenty
# pods are all failing for the same reason does not need twenty rows to say so.
MAX_BLOCKERS = 3


@dataclass(frozen=True)
class Completed:
    """One command's outcome. A named type rather than a tuple, as everything here is."""

    ok: bool
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Observation:
    """One tick's worth of facts, before anything has been decided about them."""

    unit_state: str = "unknown"
    reachable: bool = False
    namespace_present: bool = False
    workloads: list[Workload] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    detail: str = ""


class Commands:
    """Everything that leaves this process.

    A class rather than three module-level functions so the tests can hand `Cluster`
    another one. Injecting the runner is what keeps the suite free of monkeypatching:
    nothing is replaced behind the code's back, the seam is an argument.
    """

    def run(self, argv: list[str]) -> Completed:
        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_S,
            )
        except (subprocess.SubprocessError, OSError) as error:
            logger.debug("%s: %s", argv[0], error)
            return Completed(ok=False, stdout="", stderr=str(error))
        return Completed(
            ok=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr.strip(),
        )


class Cluster:
    """The impure half: what this box can see of its own bring-up."""

    def __init__(
        self,
        namespace: str,
        unit: str,
        kubeconfig: str | None = None,
        commands: Commands | None = None,
    ):
        self._namespace = namespace
        self._unit = unit
        self._kubeconfig = kubeconfig
        self._commands = commands or Commands()

    def observe(self) -> Observation:
        """One tick. Cheap while the box is waiting, three calls at its most expensive."""
        unit_state = self._unit_state()

        namespace = self._kubectl(
            ["get", "namespace", self._namespace], namespaced=False
        )
        if not namespace.ok:
            # Told apart rather than folded together: "the cluster is not answering yet"
            # and "the cluster is answering and Loom has not been deployed into it" are
            # fixed by different things and take different amounts of time.
            missing = "not found" in namespace.stderr.lower()
            return Observation(
                unit_state=unit_state,
                reachable=missing,
                namespace_present=False,
                detail=namespace.stderr,
            )

        listing = self._kubectl(["get", WORKLOAD_KINDS, "--output", "json"])
        if not listing.ok:
            return Observation(
                unit_state=unit_state,
                reachable=True,
                namespace_present=True,
                detail=listing.stderr,
            )

        workloads = parse_workloads(_items(listing.stdout))
        blockers: list[Blocker] = []
        # Only when something is actually outstanding. On a box that has been up for a
        # week this halves the poll, and the answer would be empty anyway.
        if any(w.counted and not w.converged for w in workloads):
            pods = self._kubectl(["get", "pods", "--output", "json"])
            if pods.ok:
                blockers = parse_blockers(_items(pods.stdout))

        return Observation(
            unit_state=unit_state,
            reachable=True,
            namespace_present=True,
            workloads=workloads,
            blockers=blockers,
        )

    def _unit_state(self) -> str:
        completed = self._commands.run(
            ["systemctl", "show", "--property=ActiveState", "--value", self._unit]
        )
        if not completed.ok:
            return "unknown"
        return completed.stdout.strip() or "unknown"

    def _kubectl(self, arguments: list[str], namespaced: bool = True) -> Completed:
        argv = ["kubectl", f"--request-timeout={REQUEST_TIMEOUT}"]
        if self._kubeconfig:
            argv += ["--kubeconfig", self._kubeconfig]
        if namespaced:
            argv += ["--namespace", self._namespace]
        return self._commands.run(argv + arguments)


def _items(document: str) -> list[object]:
    try:
        raw = json.loads(document)
    except ValueError:
        return []
    items = _mapping(raw).get("items")
    return items if isinstance(items, list) else []


def _mapping(value: object) -> dict:
    """Whatever this is, as something with `.get`.

    Every field below is read out of a document kubectl produced, and kubectl is not the
    only thing that can end up on the other end of that pipe -- a proxy error page, a
    half-written file, a version that renamed a field. Missing is the normal case here,
    not an exception, so the whole parser is written in terms of "absent means default".
    """
    return value if isinstance(value, dict) else {}


def parse_workloads(items: list[object]) -> list[Workload]:
    """Every workload kubectl returned, reduced to the two numbers that matter."""
    workloads = []
    for item in items:
        if not isinstance(item, dict):
            continue
        workload = _workload(item)
        if workload is not None:
            workloads.append(workload)
    return workloads


def _workload(item: dict) -> Workload | None:
    spec = _mapping(item.get("spec"))
    status = _mapping(item.get("status"))
    name = str(_mapping(item.get("metadata")).get("name", ""))
    if not name:
        return None

    # `kubectl get a,b,c -o json` stamps each item with its own kind, which is the whole
    # reason the four kinds can be asked for in one call. A document without one is
    # sniffed rather than dropped: the fields are distinctive, and a silently skipped
    # workload would understate the denominator in a way nobody would notice.
    kind = str(item.get("kind") or _sniff_kind(spec, status))

    if kind == "DaemonSet":
        return Workload(
            kind=kind,
            name=name,
            desired=_int(status.get("desiredNumberScheduled")),
            ready=_int(status.get("numberReady")),
        )
    if kind == "Job":
        return Workload(
            kind=kind,
            name=name,
            desired=_int(spec.get("completions"), default=1),
            ready=_int(status.get("succeeded")),
        )
    if kind in ("Deployment", "StatefulSet"):
        return Workload(
            kind=kind,
            name=name,
            desired=_int(spec.get("replicas"), default=1),
            ready=_int(status.get("readyReplicas")),
        )
    return None


def _sniff_kind(spec: dict, status: dict) -> str:
    if "desiredNumberScheduled" in status or "numberReady" in status:
        return "DaemonSet"
    if "completions" in spec or "succeeded" in status:
        return "Job"
    return "Deployment"


def _int(value: object, default: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return int(value)


def parse_blockers(items: list[object]) -> list[Blocker]:
    """Pods that will not become ready by being waited for."""
    blockers = []
    for item in items:
        if not isinstance(item, dict):
            continue
        blocker = _blocker(item)
        if blocker is not None:
            blockers.append(blocker)
        if len(blockers) >= MAX_BLOCKERS:
            break
    return blockers


def _blocker(item: dict) -> Blocker | None:
    status = _mapping(item.get("status"))
    name = str(_mapping(item.get("metadata")).get("name", ""))
    if not name:
        return None

    phase = str(status.get("phase", ""))
    # A finished Job's pod. Not a problem, and the Job itself is already counted.
    if phase == "Succeeded":
        return None

    containers = status.get("containerStatuses")
    if isinstance(containers, list):
        for container in containers:
            waiting = _mapping(_mapping(container).get("state")).get("waiting")
            reason = str(_mapping(waiting).get("reason", ""))
            if reason in FATAL_WAITING_REASONS:
                return Blocker(pod=name, reason=reason)

    # Nothing wrong with the containers, because there are none: the scheduler has
    # nowhere to put this pod. On an appliance that is almost always memory, and it is
    # the failure a percentage hides most completely -- nothing is crashing, nothing is
    # pulling, the count simply never moves.
    if phase == "Pending":
        conditions = status.get("conditions")
        if isinstance(conditions, list):
            for raw in conditions:
                condition = _mapping(raw)
                if (
                    condition.get("type") == "PodScheduled"
                    and condition.get("status") == "False"
                ):
                    return Blocker(
                        pod=name, reason=str(condition.get("reason") or "Unschedulable")
                    )
    return None


def tally(workloads: list[Workload]) -> Counts:
    """Replicas ready out of replicas wanted, over the workloads that count."""
    counted = [workload for workload in workloads if workload.counted]
    return Counts(
        ready=sum(min(workload.ready, workload.desired) for workload in counted),
        total=sum(workload.desired for workload in counted),
    )


def classify(observation: Observation, previous: Stage | None = None) -> Stage:
    """Which stage one observation puts the box in.

    `previous` is consulted for one thing only: telling a box that has never been ready
    apart from one that was and is not any more. Everything else is a function of what is
    true now.
    """
    if observation.unit_state == "failed":
        return Stage.FAILED

    if not observation.reachable or not observation.namespace_present:
        return Stage.WAITING

    # Deliberately the same condition console.nix's pane used to evaluate for itself:
    # the unit is Type=oneshot with RemainAfterExit, so it reads `activating` for the
    # hours of a bring-up and `active` only once up.sh has exited 0.
    settled = observation.unit_state == "active"
    if not settled:
        return Stage.DEPLOYING

    counted = [workload for workload in observation.workloads if workload.counted]
    converged = bool(counted) and all(workload.converged for workload in counted)
    if converged:
        return Stage.READY

    # up.sh has returned and something is not ready. Before the box has ever been ready
    # that is an ordinary rollout; afterwards it is a regression, and the two deserve
    # different words on a screen somebody walks up to.
    if previous in (Stage.READY, Stage.DEGRADED):
        return Stage.DEGRADED
    return Stage.ROLLING_OUT
