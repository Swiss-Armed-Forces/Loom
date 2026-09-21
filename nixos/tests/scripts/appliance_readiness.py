"""Readiness: how far the bring-up has got, on the three screens that show it.

Its own file rather than another hundred lines of scripts/appliance.py, which boots the
same VM and was already at pylint's module-length ceiling. tests/appliance.nix inlines
both, so this is one more section of that test rather than a second machine to boot --
and `check_readiness` is called from `run()` there.

There is no cluster in this VM and never will be, so what is exercised here is the half
that has to work when there is not one: the publisher says `waiting` rather than dying,
the banner stays the height it was, the status line says something anyway, and typing
`loom-ready` reports failure. The rules that turn a real cluster's documents into a
stage are pure functions with a suite of their own -- nixos/ready/tests -- which is
where every case this VM cannot produce is covered.
"""

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from driver import Machine, Subtest


def _status_line(appliance: "Machine") -> str:
    """The bottom row of tty1, which is where tmux draws its status line.

    /dev/vcsa1 is the VT's own memory: two bytes per cell, character then attribute,
    behind a four-byte header of rows, columns and the cursor position. Non-printing
    cells come back as spaces -- the colours are not what is being asserted.
    """
    raw = base64.b64decode(appliance.succeed("base64 -w0 /dev/vcsa1"))
    rows, columns = raw[0], raw[1]
    body = raw[4:]
    offset = (rows - 1) * columns
    return "".join(
        (
            chr(body[(offset + column) * 2])
            if 32 <= body[(offset + column) * 2] < 127
            else " "
        )
        for column in range(columns)
    )


def check_readiness(appliance: "Machine", subtest: "Subtest", operator: str) -> None:
    """The publisher, the banner line, the status segment and the one-shot."""
    with subtest("readiness is published for the pane, the status line and the banner"):
        appliance.wait_for_unit("loom-ready.service")
        appliance.wait_for_file("/run/loom/ready/state.json")
        appliance.wait_for_file("/run/loom/ready/summary")

        # Read with `jq` rather than parsed here, and not only to keep `import json`
        # out of a file the driver concatenates with scripts/appliance.py -- which
        # already imports it, and ruff rejects the pair. It also asserts the box wrote
        # something that is JSON at all, from the box, which a `cat` into Python does
        # not: the readers are two tmux panes and a shell script, none of which would
        # survive being handed a half-written document.
        stage = appliance.succeed("jq -r .stage /run/loom/ready/state.json").strip()
        # No cluster here. The point is that this is a stage rather than a crash: the
        # publisher starts with the box, long before minikube exists, and has to keep
        # saying something sensible for the hours a first bring-up takes.
        assert stage == "waiting", stage
        counts = appliance.succeed(
            "jq -r '.counts.ready, .counts.total' /run/loom/ready/state.json"
        ).split()
        assert counts == ["0", "0"], counts

        # Both readers run as the operator -- two of them are spawned by the tmux
        # server -- while the writer is root, so neither file may be root-only.
        for path in ["/run/loom/ready/state.json", "/run/loom/ready/summary"]:
            mode = appliance.succeed(f"stat -c %a {path}").strip()
            assert mode.endswith("4") or mode.endswith("6"), f"{path} is {mode}"

    with subtest("the banner costs no row until it has something to report"):
        # Empty while the cluster has not answered, which is the whole of this VM's
        # life. The banner is written straight to the VT with no paging, so a line too
        # many scrolls the Loom mark off the top -- and on a --wifi box a QR code is
        # already competing for those rows.
        assert appliance.succeed("cat /run/loom/ready/summary").strip() == ""
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        assert "Loom:" not in issue, issue

    with subtest("a box that has got somewhere says so on the login screen"):
        # The stage this VM cannot reach on its own, published by hand. The unit is
        # stopped first because it would overwrite the record within one poll -- and
        # this is also how a human demonstrates the whole display without a cluster.
        appliance.succeed("systemctl stop loom-ready.service")
        appliance.succeed(
            "printf 'Loom: starting -- 12/18 pods ready.\\n'"
            " >/run/loom/ready/summary"
        )

        # loom-banner-refresh rewrites the issue; the operator is logged in by now, so
        # it must NOT restart the getty -- that would blank the session somebody is
        # sitting in, which on a box whose console is the entire user interface is the
        # worst thing this feature could do. Exit 1 is how it says it did not.
        status, _ = appliance.execute("loom-banner-refresh")
        assert status == 1, "redrew the login screen under a logged-in operator"

        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        assert "Loom: starting -- 12/18 pods ready." in issue, issue
        # That the line can never carry a backslash -- an agetty escape, eaten before
        # anybody sees it (box.nix) -- is asserted where it is generated, against every
        # stage at once: nixos/ready/tests/test_summary.py.

        appliance.succeed("systemctl start loom-ready.service")
        appliance.wait_until_succeeds(
            'test -z "$(cat /run/loom/ready/summary)"',
        )

    with subtest("the status line carries readiness for the life of the session"):
        # The pane's bar goes when the pane becomes k9s; this is what is left.
        status_left = appliance.succeed(
            "tmux -S /run/loom/tmux.sock show-options -gv status-left"
        ).strip()
        assert "loom-ready" in status_left, status_left
        # tmux's default status-left-length is ten characters -- two more than
        # "  LOOM  " -- and it is applied to the *expanded* line, not to the format
        # above, so left alone it would cut the segment off entirely. The budget has to
        # cover the longest thing the segment can expand to.
        length = int(
            appliance.succeed(
                "tmux -S /run/loom/tmux.sock show-options -gv status-left-length"
            ).strip()
        )
        assert length > len("  LOOM  degraded 17/18  "), length

        # On the screen, not merely in the configuration -- read off the VT the way
        # tests/scripts/appliance_wifi.py reads the banner. `display-message -p` with
        # `#{E:status-left}` looks like the cheaper check and is not one: `#()` is run
        # by the status line's own drawing code, and a fresh format tree expands it to
        # nothing and never asks again, so that assertion can only ever time out.
        #
        # Polled, because the status line redraws on `status-interval`, and bounded, so
        # a segment that never appears fails here in a minute rather than in the
        # driver's fifteen.
        line = ""
        for _ in range(30):
            line = _status_line(appliance)
            if "starting" in line:
                break
            appliance.sleep(2)
        else:
            raise AssertionError(f"no readiness on the status line: {line!r}")
        assert "LOOM" in line, line

    with subtest("loom-ready reports failure on a box that is not up"):
        # Typed at an Alt-F2 prompt, and by anything scripting against it. A box with
        # no cluster must not exit 0 from a command whose whole question is whether
        # Loom is serving.
        status, output = appliance.execute(f"runuser -u {operator} -- loom-ready")
        assert status != 0, output
        assert "waiting for the cluster" in output, output
