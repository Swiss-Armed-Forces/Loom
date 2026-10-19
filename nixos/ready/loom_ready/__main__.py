"""`loom-ready`: one program, four jobs, because they are four views of one answer.

    loom-ready --publish    the root unit that works it out and writes it down
    loom-ready --pane       the console session's bring-up pane
    loom-ready --oneline    the tmux status line's segment
    loom-ready              typed at a prompt: the panel, plus what is outstanding

Only `--publish` talks to the cluster as a matter of course. `--oneline` never does -- it
runs from the tmux server every few seconds and must not be able to block it -- and the
default reads the published record too, falling back to asking the cluster itself only
when nothing is publishing one (a box being debugged, an operator who stopped the unit).

The defaults come from the environment rather than being written out here, and ready.nix
sets them on the wrapper. `loom` looks like a safe default for the namespace right up
until somebody changes NAMESPACE in vars.sh, at which point a command that quietly
defaulted would report on a namespace that does not exist -- so the values are passed in
from the one place that knows them, the same route console.nix takes for the pane.
"""

import argparse
import logging
import os
import sys
import time

from rich.console import Console

from loom_ready import render, text
from loom_ready.cluster import Cluster, classify, tally
from loom_ready.pane import Pane, PaneSettings
from loom_ready.publish import DEFAULT_INTERVAL_S, Publisher, PublishSettings
from loom_ready.state import Readiness, Stage, read

DEFAULT_STATE_DIR = os.environ.get("LOOM_READY_STATE_DIR", "/run/loom/ready")
DEFAULT_NAMESPACE = os.environ.get("LOOM_READY_NAMESPACE", "loom")
DEFAULT_UNIT = os.environ.get("LOOM_READY_UNIT", "loom.service")
DEFAULT_KUBECONFIG = os.environ.get("LOOM_READY_KUBECONFIG") or None


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if arguments.verbose else logging.INFO,
        format="%(message)s",
    )

    if arguments.publish:
        return _publish(arguments)
    if arguments.pane:
        return _pane(arguments)
    if arguments.oneline:
        return _oneline(arguments)
    return _report(arguments)


def _publish(arguments: argparse.Namespace) -> int:
    return Publisher(
        cluster=_cluster(arguments),
        settings=PublishSettings(
            state_dir=arguments.state_dir,
            interval=arguments.interval,
            on_change=[arguments.on_change] if arguments.on_change else [],
        ),
    ).run()


def _pane(arguments: argparse.Namespace) -> int:
    return Pane(
        PaneSettings(
            unit=arguments.unit,
            # Empty rather than absent is how console.nix says "this mode has no
            # publisher": a Nix-generated wrapper finds it far easier to interpolate an
            # empty string than to drop a flag.
            state_dir=arguments.state_dir or None,
            k9s=arguments.k9s or None,
            setup_marker=arguments.setup_marker or None,
        )
    ).run()


def _oneline(arguments: argparse.Namespace) -> int:
    # Never touches the cluster and never blocks: this runs out of the tmux server on
    # `status-interval`, and a status line that can hang is a session that can hang.
    # Nothing to say prints nothing, and the status line then looks exactly as it did
    # before any of this existed.
    line = text.tmux_oneline(read(arguments.state_dir))
    if line:
        sys.stdout.write(line)
    return 0


def _report(arguments: argparse.Namespace) -> int:
    readiness = read(arguments.state_dir)
    if readiness is None:
        readiness = _observe(arguments)

    Console().print(render.report(readiness, time.time()))
    # An exit status, so this is usable in a script and in the VM test: 0 only when the
    # box is actually up.
    return 0 if readiness is not None and readiness.stage is Stage.READY else 1


def _observe(arguments: argparse.Namespace) -> Readiness:
    """Ask the cluster directly, for when nothing is publishing.

    No `changed` timestamp: one observation cannot know when a number last moved, and
    inventing one would make the stall note lie on the first call.
    """
    observation = _cluster(arguments).observe()
    return Readiness(
        stage=classify(observation),
        counts=tally(observation.workloads),
        workloads=observation.workloads,
        blockers=observation.blockers,
        detail=observation.detail,
        updated=time.time(),
    )


def _cluster(arguments: argparse.Namespace) -> Cluster:
    return Cluster(
        namespace=arguments.namespace,
        unit=arguments.unit,
        kubeconfig=arguments.kubeconfig,
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="loom-ready",
        description="Is Loom up on this appliance, and how far along is it",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--publish",
        action="store_true",
        help="poll the cluster and publish readiness (the loom-ready.service unit)",
    )
    mode.add_argument(
        "--pane",
        action="store_true",
        help="run the console session's bring-up pane",
    )
    mode.add_argument(
        "--oneline",
        action="store_true",
        help="print the tmux status line segment and exit",
    )

    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    parser.add_argument("--unit", default=DEFAULT_UNIT)
    parser.add_argument("--kubeconfig", default=DEFAULT_KUBECONFIG)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_S)
    parser.add_argument(
        "--on-change",
        default="",
        help="command to run when the stage changes (the banner refresh)",
    )
    parser.add_argument(
        "--k9s",
        default="",
        help="--pane: what to exec once Loom is up",
    )
    parser.add_argument(
        "--setup-marker",
        default="",
        help="--pane: the file first-time setup writes when it has finished",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
