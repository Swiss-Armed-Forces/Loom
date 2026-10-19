"""The screen an operator stands in front of for the hours a box takes to come up.

Everything here is about the one thing this pane owes them: the log, on the screen, in
both boot modes. It is the assertion the package did not have when the pane grew its
panel -- the panel loop became the only reader of the journal, and the mode without a
panel showed an operator a two-line header and then nothing at all while a fetch ran for
six hours behind it.

The pane is driven through `RecordingPane` (doubles.py), which replaces one call: the
`execv` that turns the pane into k9s, because a test that let that run would be k9s.
Everything above it -- the preamble, the reading, the panel, the closing lines -- is the
code the appliance runs.
"""

import threading
import time
from dataclasses import replace

from doubles import UNIT, FakeCommands, FakeJournal, RecordingPane, unit

from loom_ready.pane import PaneSettings
from loom_ready.state import Counts, Readiness, Stage, publish
from loom_ready.text import summary

K9S = "/nix/store/whatever-k9s/bin/k9s"

# What up.sh writes while it brings the stack up, square brackets and all.
LOG = [
    "[*] Loom setup mode: populating minikube's image store.",
    "[*] Pulling docker.io/library/elasticsearch:8.13.0",
    "[+] Deployed loom-frontend",
]

ROLLING_OUT = Readiness(
    stage=Stage.ROLLING_OUT,
    counts=Counts(ready=12, total=18),
)


def setup_mode(marker: str | None = None) -> PaneSettings:
    """A first-time-setup box: a fetch to watch, no publisher, nowhere to hand over to.

    console.nix builds exactly this -- an empty `--state-dir`, which __main__ turns into
    None -- and so does a run-mode box with `loom.ready.enable = false`.
    """
    return PaneSettings(
        unit="loom-fetch.service", state_dir=None, k9s=K9S, setup_marker=marker
    )


def run_mode(state_dir: str, marker: str | None = None) -> PaneSettings:
    return PaneSettings(
        unit="loom.service", state_dir=state_dir, k9s=K9S, setup_marker=marker
    )


def commands(state: str) -> FakeCommands:
    """`systemctl show --property=ActiveState`, which is all the pane asks systemd."""
    return FakeCommands({UNIT: unit(state)})


def _turns_reach(pane: RecordingPane, turns: int) -> bool:
    """Wait until the panel loop has gone round `turns` times, or give up.

    A bound on an observable rather than a sleep: what a test about a loop that must
    not end needs is proof that it went round, and how long that takes depends on the
    machine. The deadline is generous because it is only reached when the behaviour
    under test is broken.
    """
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if pane.turns >= turns:
            return True
        time.sleep(0.01)
    return False


def publish_stage(state_dir: str, stage: Stage = Stage.ROLLING_OUT) -> None:
    """What the publisher would have written this second.

    Stamped `now` rather than with a fixed time because the readers drop a record they
    have not seen updated in three polls -- see state.STALE_AFTER_S.
    """
    now = time.time()
    record = replace(ROLLING_OUT, stage=stage, updated=now, changed=now)
    publish(state_dir, record, summary(record))


def test_the_fetch_log_reaches_a_pane_with_no_publisher_behind_it():
    """The regression this file exists for.

    Setup mode has no cluster and no panel, so it takes the short path out of `run` --
    and for one release that path opened a `journalctl` whose pipe nobody read. The
    operator got the preamble and then six hours of nothing, with the follower itself
    wedged as soon as the pipe filled.
    """
    journal = FakeJournal(LOG)
    pane = RecordingPane(setup_mode(), journal, commands=commands("activating"))

    assert pane.run() == 0
    for line in LOG:
        assert line in pane.printed(), pane.printed()


def test_a_log_line_is_never_read_as_markup():
    """up.sh prefixes every line it prints with `[*]`.

    rich reads square brackets as a style, so a console that was handed these as markup
    would drop the prefix on a good day and raise on a bad one -- on the one pane whose
    job is to show what went wrong.
    """
    journal = FakeJournal(["[*] Pulling [not-a-style] and [/closing]"])
    pane = RecordingPane(setup_mode(), journal, commands=commands("activating"))

    pane.run()
    assert "[*] Pulling [not-a-style] and [/closing]" in pane.printed()


def test_the_log_keeps_scrolling_while_the_panel_is_pinned(tmp_path):
    """Run mode reads the same journal through the same drain, above the bar."""
    state_dir = str(tmp_path)
    publish_stage(state_dir, Stage.DEPLOYING)
    # The box becomes ready once the log has been drawn, which is what ends the loop.
    journal = FakeJournal(LOG, then=lambda: publish_stage(state_dir))
    pane = RecordingPane(run_mode(state_dir), journal, commands=commands("activating"))

    assert pane.run() == 0
    for line in LOG:
        assert line in pane.printed(), pane.printed()


def test_the_pane_becomes_the_pod_list_once_the_box_is_up(tmp_path):
    """And says where the log went, because k9s draws on the alternate buffer.

    `ROLLING_OUT` rather than `READY` on purpose: the handover is "up.sh has returned
    and the namespace exists", which is well before every pod is ready. An operator who
    had to wait for READY would watch a finished log for the length of a rollout.
    """
    state_dir = str(tmp_path)
    publish_stage(state_dir)
    journal = FakeJournal(LOG)
    pane = RecordingPane(run_mode(state_dir), journal, commands=commands("active"))

    assert pane.run() == 0
    assert pane.became == K9S
    # Left following a unit nobody is reading, journalctl would sit there for the life of
    # the box behind the pod list.
    assert journal.stopped
    assert "journalctl --unit loom.service --follow" in pane.printed()


def test_a_bring_up_that_failed_keeps_its_log_on_the_screen(tmp_path):
    """The one time the log must not be replaced by a pod list.

    Really an assertion about the pane trusting `Readiness.settled`: FAILED is not in
    it, so the loop does not end and nothing hands over. Run on a thread because that
    loop has no other way to stop -- which is the behaviour under test.
    """
    state_dir = str(tmp_path)
    publish_stage(state_dir, Stage.FAILED)
    drained = threading.Event()
    journal = FakeJournal(LOG, then=drained.set)
    pane = RecordingPane(run_mode(state_dir), journal, commands=commands("failed"))

    thread = threading.Thread(target=pane.run, daemon=True)
    thread.start()
    assert drained.wait(timeout=5), "the journal was never read"
    # Waited for, not slept through: the assertion below is only worth anything
    # once the loop has demonstrably gone round without handing over, and a fixed
    # sleep proves that on a fast machine and nothing at all on a loaded one. Two
    # turns is one full pass through the handover check and back.
    assert _turns_reach(pane, 2), f"the panel loop stopped after {pane.turns} turns"

    assert pane.became is None
    assert "loom.service FAILED" in pane.printed()
    for line in LOG:
        assert line in pane.printed(), pane.printed()

    # Retire the loop rather than leave it spinning for the rest of the suite. Nothing
    # takes a real box from a failed bring-up to settled; this only ends the thread.
    publish_stage(state_dir)
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_the_power_off_warning_is_setup_modes_alone(tmp_path):
    """The marker outlives the mode that wrote it.

    `.loom-setup-complete` sits in the repo directory of the installed box, and run mode
    is a boot entry of that same box -- so a run-mode pane that consulted it would tell
    an operator their appliance powers itself off when it has finished, which is what
    setup mode does and this mode never will.
    """
    marker = tmp_path / ".loom-setup-complete"
    marker.write_text("", encoding="utf-8")
    state_dir = str(tmp_path / "ready")
    publish_stage(state_dir)

    installed = RecordingPane(
        run_mode(state_dir, marker=str(marker)),
        FakeJournal([]),
        commands=commands("inactive"),
    )
    installed.run()
    assert "powers the box" not in installed.printed()
    assert "has not started yet" in installed.printed()

    fetching = RecordingPane(
        setup_mode(marker=str(marker)),
        FakeJournal([]),
        commands=commands("inactive"),
    )
    fetching.run()
    assert "powers the box" in fetching.printed()
