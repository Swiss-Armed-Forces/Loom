"""Test doubles for the two seams this package has.

Both are passed in rather than patched into place: `Cluster` takes a `Commands`, and
`Publisher` takes a `Cluster`. Nothing here replaces anything at runtime behind the code's
back, which is the repository's standing rule about monkeypatching -- and the reason the
seams exist in the shape they do.
"""

import json

from loom_ready.cluster import Cluster, Commands, Completed, Observation

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
    """A `kubectl get ... -o json` document."""
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
