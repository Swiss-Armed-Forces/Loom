"""Test doubles for the seams this package has.

Every one of them is passed in rather than patched into place: `Cluster` takes a
`Commands`, `Publisher` takes a `Cluster`, and `Pane` takes a `Journal` and a console.
Nothing here replaces anything at runtime behind the code's back, which is the
repository's standing rule about monkeypatching -- and the reason the seams exist in the
shape they do.

The one exception is `RecordingPane`, which overrides the `execv` that ends the pane's
life. That is not a seam that can be injected: the point of the call is that nothing
runs after it.
"""

import io
import json
from collections.abc import Callable, Iterator

from rich.console import Console

from loom_ready.cluster import Cluster, Commands, Completed, Observation
from loom_ready.pane import Journal, Pane, PaneSettings, PaneTiming

# What a call is about, decided from its argv. The publisher makes at most three kinds of
# call per tick and a test wants to answer them differently.
UNIT = "unit"
NAMESPACE = "namespace"
WORKLOADS = "workloads"
PODS = "pods"

OK = Completed(ok=True, stdout="", stderr="")


class FakeCommands(Commands):
    """Canned answers, and a record of what was asked.

    The record is half the point: "the pod list is only fetched while something is
    outstanding" is a property of the poll loop that can only be observed here.
    """

    def __init__(self, answers: dict[str, Completed] | None = None):
        self.answers = answers or {}
        self.calls: list[list[str]] = []

    def run(self, argv: list[str]) -> Completed:
        self.calls.append(argv)
        return self.answers.get(kind_of(argv), Completed(False, "", "no answer"))

    def kinds(self) -> list[str]:
        return [kind_of(argv) for argv in self.calls]


def kind_of(argv: list[str]) -> str:
    line = " ".join(argv)
    if argv and argv[0] == "systemctl":
        return UNIT
    if "get namespace" in line:
        return NAMESPACE
    if "deployments" in line:
        return WORKLOADS
    if "get pods" in line:
        return PODS
    return ""


def unit(state: str) -> Completed:
    return Completed(ok=True, stdout=state + "\n", stderr="")


def listing(*items: dict) -> Completed:
    """A `kubectl get -o json` document, whatever the resources were."""
    return Completed(ok=True, stdout=json.dumps({"items": list(items)}), stderr="")


def missing_namespace(name: str = "loom") -> Completed:
    return Completed(
        ok=False,
        stdout="",
        stderr=f'Error from server (NotFound): namespaces "{name}" not found',
    )


def unreachable() -> Completed:
    return Completed(
        ok=False,
        stdout="",
        stderr="The connection to the server 192.168.49.2:8443 was refused",
    )


def deployment(name: str, desired: int = 1, ready: int = 0) -> dict:
    return {
        "kind": "Deployment",
        "metadata": {"name": name},
        "spec": {"replicas": desired},
        "status": {"readyReplicas": ready},
    }


def stateful_set(name: str, desired: int = 1, ready: int = 0) -> dict:
    return {
        "kind": "StatefulSet",
        "metadata": {"name": name},
        "spec": {"replicas": desired},
        "status": {"readyReplicas": ready},
    }


def daemon_set(name: str, desired: int = 1, ready: int = 0) -> dict:
    return {
        "kind": "DaemonSet",
        "metadata": {"name": name},
        "spec": {},
        "status": {"desiredNumberScheduled": desired, "numberReady": ready},
    }


def job(name: str, completions: int = 1, succeeded: int = 0) -> dict:
    return {
        "kind": "Job",
        "metadata": {"name": name},
        "spec": {"completions": completions},
        "status": {"succeeded": succeeded},
    }


def pod(name: str, phase: str = "Running", waiting: str | None = None) -> dict:
    status: dict = {"phase": phase}
    if waiting is not None:
        status["containerStatuses"] = [{"state": {"waiting": {"reason": waiting}}}]
    return {"kind": "Pod", "metadata": {"name": name}, "status": status}


def unschedulable(name: str, reason: str = "Unschedulable") -> dict:
    return {
        "kind": "Pod",
        "metadata": {"name": name},
        "status": {
            "phase": "Pending",
            "conditions": [
                {"type": "PodScheduled", "status": "False", "reason": reason}
            ],
        },
    }


class FakeJournal(Journal):
    """Canned log lines, and whether the pane stopped following them.

    A subclass for the same reason `StubCluster` is one: `Pane` keeps its real
    constructor, so the tests cannot drift from it. A real journal under `--follow`
    never ends; this one does, which is what lets a test assert on everything the pane
    printed.

    `then` runs once the last line has been yielded. That is how a test makes the box
    become ready at a moment it chooses -- after the log has been drawn -- rather than
    racing the panel's own poll for it.
    """

    def __init__(self, lines: list[str], then: Callable[[], None] | None = None):
        super().__init__(unit="test.service")
        self._lines = list(lines)
        self._then = then
        self.stopped = False

    def lines(self) -> Iterator[str]:
        yield from self._lines
        if self._then is not None:
            self._then()

    def stop(self) -> None:
        self.stopped = True


class RecordingPane(Pane):
    """A pane that records the handover instead of performing it.

    `_become` is `os.execv`, which does not return; a test that let it run would be
    replaced by k9s, and there is no k9s here. Overriding the one call keeps everything
    above it -- the preamble, the log, the panel, the closing lines -- exactly the code
    the appliance runs.
    """

    def __init__(self, settings: PaneSettings, journal: Journal, **kwargs):
        # Wide enough that nothing the pane prints is wrapped mid-word, since the
        # assertions are about the words.
        self.screen = io.StringIO()
        kwargs.setdefault("console", Console(file=self.screen, width=120))
        # Quick enough that a case costs milliseconds rather than the six seconds the
        # real waits add up to. See PaneTiming.
        kwargs.setdefault("timing", PaneTiming(refresh=0.01, handover_grace=0.0))
        super().__init__(settings, journal=journal, **kwargs)
        self.became: str | None = None

    def _become(self, program: str) -> int:
        self.became = program
        return 0

    def printed(self) -> str:
        """Everything this pane put on the screen."""
        return self.screen.getvalue()


class StubCluster(Cluster):
    """A cluster that returns the observations a test hands it, in order.

    A subclass rather than a separate object so that `Publisher` keeps its real type and
    the tests cannot drift from the constructor they are standing in for. The last
    observation repeats once the script runs out, which is what lets a test tick several
    times at one stage.
    """

    def __init__(self, observations: list[Observation]):
        super().__init__(namespace="loom", unit="loom.service")
        self.observations = list(observations)
        self.observed = 0

    def observe(self) -> Observation:
        index = min(self.observed, len(self.observations) - 1)
        self.observed += 1
        return self.observations[index]
