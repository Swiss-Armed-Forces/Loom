"""Which stage a box is in, and what the console does about it.

The stage is the frame the whole display hangs on: it picks the words on the banner, the
colour in the status line, and -- through `Readiness.settled` -- the moment the bring-up
pane hands the screen over to k9s. That last one is why this file matters more than it
looks: it is the appliance's definition of "Loom is up", and it used to be written out
twice.
"""

import doubles

from loom_ready.cluster import Observation, classify
from loom_ready.publish import Publisher, PublishSettings
from loom_ready.state import SETTLED_STAGES, Counts, Stage, Workload, read


def observation(
    unit_state: str = "active",
    reachable: bool = True,
    namespace_present: bool = True,
    workloads: list[Workload] | None = None,
) -> Observation:
    return Observation(
        unit_state=unit_state,
        reachable=reachable,
        namespace_present=namespace_present,
        workloads=workloads if workloads is not None else [],
    )


def workload(desired: int = 1, ready: int = 1, name: str = "api") -> Workload:
    return Workload(kind="Deployment", name=name, desired=desired, ready=ready)


def test_no_cluster_is_waiting():
    assert (
        classify(observation(reachable=False, namespace_present=False)) is Stage.WAITING
    )


def test_cluster_without_the_namespace_is_still_waiting():
    """Minikube is up and up.sh has not deployed yet.

    Different cause, same screen.
    """
    assert classify(observation(namespace_present=False)) is Stage.WAITING


def test_a_failed_unit_outranks_everything():
    """Including a cluster that looks perfectly healthy.

    up.sh can fail after deploying most of the stack, and a box that says "ready" with a
    failed bring-up behind it is the single most misleading thing this could print.
    """
    assert (
        classify(observation(unit_state="failed", workloads=[workload()]))
        is Stage.FAILED
    )


def test_bring_up_still_running_is_deploying():
    """`activating` is hours of work on these boxes, and the denominator is still
    growing."""
    assert classify(observation(unit_state="activating")) is Stage.DEPLOYING


def test_up_returned_but_pods_outstanding_is_rolling_out():
    assert (
        classify(observation(workloads=[workload(desired=3, ready=1)]))
        is Stage.ROLLING_OUT
    )


def test_everything_converged_is_ready():
    assert (
        classify(observation(workloads=[workload(), workload(name="frontend")]))
        is Stage.READY
    )


def test_an_empty_namespace_is_not_ready():
    """`all()` over nothing is True, which would make a bare namespace look finished.

    This is exactly the window up.sh spends creating the namespace before applying
    anything into it.
    """
    assert classify(observation(workloads=[])) is Stage.ROLLING_OUT


def test_idle_workloads_alone_are_not_ready():
    """A namespace holding nothing but KEDA-scaled-to-zero Deployments."""
    assert (
        classify(observation(workloads=[workload(desired=0, ready=0)]))
        is Stage.ROLLING_OUT
    )


def test_falling_out_of_ready_is_degraded_not_rolling_out():
    """A pod that starts crash-looping on Tuesday is not a bring-up."""
    assert (
        classify(observation(workloads=[workload(ready=0)]), previous=Stage.READY)
        is Stage.DEGRADED
    )
    assert (
        classify(observation(workloads=[workload(ready=0)]), previous=Stage.DEGRADED)
        is Stage.DEGRADED
    )


def test_recovering_from_degraded_reaches_ready_again():
    assert (
        classify(observation(workloads=[workload()]), previous=Stage.DEGRADED)
        is Stage.READY
    )


def test_settled_is_exactly_the_old_handover_condition():
    """What the pane waits for before giving the screen to k9s.

    console.nix used to evaluate "the unit is active and the namespace exists" in the
    pane itself. That is precisely these three stages, and stating it once is what keeps
    the pane, the status line and the banner from disagreeing about whether Loom is up.
    """
    settled = {stage for stage in Stage if stage in SETTLED_STAGES}
    assert settled == {Stage.ROLLING_OUT, Stage.READY, Stage.DEGRADED}
    assert Stage.DEPLOYING not in SETTLED_STAGES
    assert Stage.WAITING not in SETTLED_STAGES
    assert Stage.FAILED not in SETTLED_STAGES


def test_the_banner_is_refreshed_on_a_stage_change_and_not_otherwise(tmp_path):
    """The banner is rendered once per boot; something has to tell it to try again.

    On a count change it must NOT: the numbers move several times a minute during a
    rollout, and each refresh restarts tty1's getty.
    """
    commands = doubles.FakeCommands()
    cluster = doubles.StubCluster(
        [
            observation(unit_state="activating"),
            observation(unit_state="activating"),
            observation(workloads=[workload(desired=3, ready=1)]),
            observation(workloads=[workload(desired=3, ready=2)]),
            observation(workloads=[workload(desired=3, ready=3)]),
        ]
    )
    publisher = Publisher(
        cluster=cluster,
        settings=PublishSettings(
            state_dir=str(tmp_path), on_change=["loom-banner-refresh"]
        ),
        commands=commands,
    )

    stages = [publisher.tick(now=100.0 + tick).stage for tick in range(5)]

    assert stages == [
        Stage.DEPLOYING,
        Stage.DEPLOYING,
        Stage.ROLLING_OUT,
        Stage.ROLLING_OUT,
        Stage.READY,
    ]
    # Two, not three. The first stage a box reaches is deliberately not refreshed: at
    # boot, box.nix's loom-banner-repaint is already redrawing the screen for a minute
    # while the console resizes under it, and it picks up whatever has been published by
    # then. A refresh here would be a second getty restart inside that window -- and a
    # getty restart eats the keypress that opens the operator's session.
    assert len(commands.calls) == 2
    assert commands.calls[0] == ["loom-banner-refresh"]


def test_the_stall_clock_only_moves_when_the_numbers_do(tmp_path):
    """ "no change for 14m" has to mean the count, not the record."""
    cluster = doubles.StubCluster(
        [
            observation(workloads=[workload(desired=3, ready=1)]),
            observation(workloads=[workload(desired=3, ready=1)]),
            observation(workloads=[workload(desired=3, ready=2)]),
        ]
    )
    publisher = Publisher(cluster=cluster, settings=PublishSettings(str(tmp_path)))

    first = publisher.tick(now=100.0)
    second = publisher.tick(now=200.0)
    third = publisher.tick(now=300.0)

    assert first.changed == 100.0
    assert (
        second.changed == 100.0
    ), "the count did not move, so the clock must not either"
    assert third.changed == 300.0
    assert second.stalled_for(now=250.0) == 150.0


def test_a_tick_is_readable_by_the_other_half(tmp_path):
    """The publisher and the readers share a directory and nothing else."""
    cluster = doubles.StubCluster(
        [observation(workloads=[workload(desired=2, ready=1)])]
    )
    Publisher(cluster=cluster, settings=PublishSettings(str(tmp_path))).tick(now=1000.0)

    record = read(str(tmp_path), now=1000.0)
    assert record is not None
    assert record.stage is Stage.ROLLING_OUT
    assert record.counts == Counts(ready=1, total=2)
