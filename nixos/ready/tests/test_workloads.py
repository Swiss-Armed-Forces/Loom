"""What the cluster's documents are read as.

Every rule here decides what the bar shows, and every one of them was chosen against a
specific thing the Loom chart does -- KEDA scaling a Deployment to zero, an init Job
that reaches Succeeded rather than Ready, a StatefulSet rolling one ordinal at a time.
They are tested against those documents rather than against invented ones.
"""

import doubles

from loom_ready.cluster import Cluster, parse_blockers, parse_workloads, tally
from loom_ready.state import Counts


def test_deployment_counts_replicas_not_objects():
    """A StatefulSet at 1 of 3 is a third of the way, not all or nothing."""
    workloads = parse_workloads(
        [doubles.stateful_set("elasticsearch", desired=3, ready=1)]
    )
    assert tally(workloads) == Counts(ready=1, total=3)


def test_missing_status_reads_as_nothing_ready():
    """A Deployment kubectl has only just accepted has no readyReplicas at all."""
    raw = doubles.deployment("api")
    del raw["status"]["readyReplicas"]
    workloads = parse_workloads([raw])
    assert workloads[0].ready == 0
    assert workloads[0].desired == 1


def test_keda_idle_deployment_is_not_counted():
    """The failure this rule exists for: a bar that can never reach the end.

    charts/templates/worker/_scaledobjects.yaml lets KEDA scale a Deployment down to
    minReplicas, which may be zero. That is the healthy steady state of an idle box, not
    something to wait for -- counted, it would hold the bar short of the end forever.
    """
    workloads = parse_workloads(
        [
            doubles.deployment("api", desired=1, ready=1),
            doubles.deployment("worker-index", desired=0, ready=0),
        ]
    )
    assert [workload.counted for workload in workloads] == [True, False]
    assert tally(workloads) == Counts(ready=1, total=1)


def test_job_is_complete_by_succeeded_not_by_ready():
    """Init Jobs gate everything and never become Ready."""
    workloads = parse_workloads(
        [
            doubles.job("init-elasticsearch", completions=1, succeeded=1),
            doubles.job("init-s3", completions=1, succeeded=0),
        ]
    )
    assert [workload.converged for workload in workloads] == [True, False]


def test_job_without_completions_wants_one():
    raw = doubles.job("generate-secret")
    del raw["spec"]["completions"]
    assert parse_workloads([raw])[0].desired == 1


def test_daemon_set_reads_its_own_fields():
    workloads = parse_workloads(
        [doubles.daemon_set("node-exporter", desired=1, ready=1)]
    )
    assert workloads[0].converged


def test_kind_is_sniffed_when_the_document_does_not_carry_one():
    """Not every path through kubectl stamps `kind` on an item.

    Dropping such an item would understate the denominator, which is the one error here
    nobody would ever notice: the bar would simply finish early.
    """
    raw = doubles.job("init-s3", completions=1, succeeded=0)
    del raw["kind"]
    workloads = parse_workloads([raw])
    assert workloads[0].kind == "Job"
    assert workloads[0].desired == 1


def test_junk_is_skipped_rather_than_fatal():
    """The other end of this pipe is not always kubectl."""
    assert not parse_workloads(["", None, {}, {"metadata": {}}])


def test_ready_above_desired_does_not_overshoot():
    """A Deployment mid-scale-down reports more ready than it wants."""
    workloads = parse_workloads([doubles.deployment("api", desired=1, ready=3)])
    assert tally(workloads) == Counts(ready=1, total=1)


def test_blockers_name_the_pod_and_the_reason():
    blockers = parse_blockers(
        [
            doubles.pod("loom-api-1", phase="Running"),
            doubles.pod("loom-ollama-0", waiting="ImagePullBackOff"),
        ]
    )
    assert [(b.pod, b.reason) for b in blockers] == [
        ("loom-ollama-0", "ImagePullBackOff")
    ]


def test_finished_job_pods_are_not_blockers():
    assert not parse_blockers([doubles.pod("loom-init-s3-abc", phase="Succeeded")])


def test_transient_waiting_reasons_are_not_blockers():
    """ContainerCreating is what a healthy pod does for a few seconds."""
    assert not parse_blockers([doubles.pod("loom-api-1", waiting="ContainerCreating")])


def test_unschedulable_pods_are_blockers():
    """The failure a percentage hides best: nothing crashes, the number just stops."""
    blockers = parse_blockers([doubles.unschedulable("loom-worker-1", "Unschedulable")])
    assert blockers[0].reason == "Unschedulable"


def test_blockers_are_capped():
    pods = [doubles.pod(f"loom-{i}", waiting="CrashLoopBackOff") for i in range(10)]
    assert len(parse_blockers(pods)) == 3


def test_pods_are_only_fetched_while_something_is_outstanding():
    """On a box that has been up for a week, half the poll is pointless."""
    commands = doubles.FakeCommands(
        {
            doubles.UNIT: doubles.unit("active"),
            doubles.NAMESPACE: doubles.OK,
            doubles.WORKLOADS: doubles.listing(
                doubles.deployment("api", desired=1, ready=1)
            ),
            doubles.PODS: doubles.listing(),
        }
    )
    Cluster("loom", "loom.service", commands=commands).observe()
    assert doubles.PODS not in commands.kinds()

    commands = doubles.FakeCommands(
        {
            doubles.UNIT: doubles.unit("active"),
            doubles.NAMESPACE: doubles.OK,
            doubles.WORKLOADS: doubles.listing(
                doubles.deployment("api", desired=1, ready=0)
            ),
            doubles.PODS: doubles.listing(
                doubles.pod("api", waiting="CrashLoopBackOff")
            ),
        }
    )
    observation = Cluster("loom", "loom.service", commands=commands).observe()
    assert doubles.PODS in commands.kinds()
    assert observation.blockers[0].reason == "CrashLoopBackOff"


def test_every_kubectl_call_carries_a_request_timeout():
    """A poll loop built out of two-minute hangs is not a poll loop.

    The interesting failure is a kubeconfig pointing at a minikube that is not running,
    where kubectl's default is to hang for two minutes per attempt -- so the pane prints
    nothing, which reads as frozen. Same trap console.nix documents for loom-k9s.
    """
    commands = doubles.FakeCommands({doubles.UNIT: doubles.unit("inactive")})
    Cluster("loom", "loom.service", commands=commands).observe()
    kubectl_calls = [argv for argv in commands.calls if argv[0] == "kubectl"]
    assert kubectl_calls
    for argv in kubectl_calls:
        assert "--request-timeout=5s" in argv, argv


def test_kubeconfig_is_passed_when_given():
    """The unit runs as root and borrows the operator's client certificates."""
    commands = doubles.FakeCommands({doubles.UNIT: doubles.unit("inactive")})
    Cluster(
        "loom", "loom.service", kubeconfig="/home/loom/.kube/config", commands=commands
    ).observe()
    kubectl = next(argv for argv in commands.calls if argv[0] == "kubectl")
    assert "--kubeconfig" in kubectl
    assert "/home/loom/.kube/config" in kubectl
