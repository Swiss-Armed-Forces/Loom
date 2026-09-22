"""How far the bring-up has got, on the screens that show it.

There is no cluster in this VM and never will be, so what is exercised here is the half
that has to work when there is not one: the publisher says `waiting` rather than dying,
the status line says something anyway, and typing `loom-ready` reports failure. The
rules that turn a real cluster's documents into a stage are pure functions with a suite
of their own -- nixos/ready/tests -- which is where every case this VM cannot produce is
covered.

The banner is the third screen, and it is asserted in `banner.py` with the rest of what
that screen carries.
"""

from typing import TYPE_CHECKING

from loom_tests import tmux, vt
from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest

STATE = "/run/loom/ready/state.json"
SUMMARY = "/run/loom/ready/summary"

# What the segment can expand to at its longest, which is the budget the status line has
# to leave for it.
WIDEST = "  LOOM  degraded 17/18  "


def published(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("readiness is published for the pane, the status line and the banner"):
        appliance.wait_for_unit("loom-ready.service")
        appliance.wait_for_file(STATE)
        appliance.wait_for_file(SUMMARY)

        # Read with `jq`, on the box, rather than parsed here: that asserts what was
        # written is JSON at all. The readers are two tmux panes and a shell script,
        # none of which would survive being handed a half-written document.
        stage = appliance.succeed(f"jq -r .stage {STATE}").strip()
        # No cluster here. The point is that this is a stage rather than a crash: the
        # publisher starts with the box, long before minikube exists, and has to keep
        # saying something sensible for the hours a first bring-up takes.
        assert stage == "waiting", stage
        counts = appliance.succeed(
            f"jq -r '.counts.ready, .counts.total' {STATE}"
        ).split()
        assert counts == ["0", "0"], counts

        # Both readers run as the operator -- two of them are spawned by the tmux
        # server -- while the writer is root, so neither file may be root-only.
        for path in [STATE, SUMMARY]:
            mode = appliance.succeed(f"stat -c %a {path}").strip()
            assert mode.endswith("4") or mode.endswith("6"), f"{path} is {mode}"


def status_line(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("the status line carries readiness for the life of the session"):
        session = tmux.Session(appliance)

        # The pane's bar goes when the pane becomes k9s; this is what is left.
        status_left = session.option("status-left")
        assert "loom-ready" in status_left, status_left
        # tmux's default status-left-length is ten characters -- two more than
        # "  LOOM  " -- and it is applied to the *expanded* line, not to the format
        # above, so left alone it would cut the segment off entirely.
        assert int(session.option("status-left-length")) > len(WIDEST)

        # On the screen, not merely in the configuration. `display-message -p` with
        # `#{E:status-left}` looks like the cheaper check and is not one: `#()` is run
        # by the status line's own drawing code, and a fresh format tree expands it to
        # nothing and never asks again, so that assertion can only ever time out.
        #
        # Polled, because the status line redraws on `status-interval`, and bounded, so
        # a segment that never appears fails here in a minute rather than in the
        # driver's fifteen.
        line = ""
        for _ in range(30):
            line = vt.read(appliance).bottom()
            if "starting" in line:
                break
            appliance.sleep(2)
        else:
            raise AssertionError(f"no readiness on the status line: {line!r}")
        assert "LOOM" in line, line


def one_shot(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("loom-ready reports failure on a box that is not up"):
        # Typed at an Alt-F2 prompt, and by anything scripting against it. A box with
        # no cluster must not exit 0 from a command whose whole question is whether
        # Loom is serving.
        status, output = appliance.execute(
            f"runuser -u {params.operator.user} -- loom-ready"
        )
        assert status != 0, output
        assert "waiting for the cluster" in output, output
