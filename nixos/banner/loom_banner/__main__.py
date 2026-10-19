"""`loom-info`: what this box is, on the screen of somebody standing in front of it.

Three things run it -- `loom-issue.service` at boot, `loom-banner-repaint.service` once
the console has stopped resizing, and `loom-banner-refresh` every time what it says
stops being true -- plus an operator typing it in a pane once the console session has
covered the boot-time copy. One generator rather than copies that drift.

The facts the image was built with arrive as flags, which box.nix sets on the wrapper:
`loom` looks like a safe default for a platform name right up until somebody builds for
another box, so the values come from the one place that knows them.

The banner is always printed whole. Measuring the console and trimming to fit cannot be
made to work -- it is resized several times during boot and a reading taken between any
two of those describes a screen that no longer exists by the time agetty paints -- so a
banner taller than its console loses its top rows, which is a mild and visible failure
rather than a silent one.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from loom_banner import render, screen
from loom_banner.facts import Box, KeyGuard, Live, Paths, Portal, Wifi

# qrencode's flags, which are all load-bearing for whether a phone decodes the card.
#
# UTF8i draws each row with the half blocks, so a module is one cell wide by half a
# cell tall -- close to square on the 12x26 cell branding.nix selects, where '#' would
# be twice as tall as wide and most phones refuse it. The `i` inverts which modules
# the glyphs stand for, so with the card's black-on-white it comes out as dark modules
# on a white field rather than white marks on whatever the console's background is.
# Two modules of quiet zone is under the four the spec asks for, but the zone here is
# white against a black console, which is the high-contrast case scanners cope with.
QRENCODE_FLAGS = ["--type=UTF8i", "--level=L", "--margin=2"]


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv if argv is not None else sys.argv[1:])
    box = _box(arguments)
    live = Live.read(_paths(arguments))

    colour = render.Colour.decide(sys.stdout)
    console = render.console(sys.stdout, colour)

    _mark(arguments, colour)

    composed = screen.compose(box, live, painted=_painted(), qr=_qr(arguments))
    for line in composed.identity:
        console.print(render.note(line))
    for section in composed.sections:
        console.print("")
        console.print(render.rule(section.title, style=section.style))
        for row in section.rows:
            console.print(render.row(row.label, row.value, secret=row.secret))
        for note in section.notes:
            console.print(render.note(note))
        for card in render.card(section.card):
            console.print(card)

    # The danger block is a fragment of its own on the login screen, so that it sorts
    # last and cannot scroll away. A hand-run has no fragments, and an operator typing
    # this on a --debug box is owed the same warning.
    if not arguments.for_issue and arguments.warning:
        console.print("")
        for warning in render.danger(arguments.warning):
            console.print(warning)

    console.print("")
    return 0


def _mark(arguments: argparse.Namespace, colour: render.Colour) -> None:
    """The mark the boot splash just showed, in the form a console can hold.

    Written raw rather than through rich: the amber is a palette redefinition, not an
    SGR colour, and the art itself comes from `loom-eyes` so that this screen, the
    installer menu and the splash all draw it from one place.
    """
    out = sys.stdout
    out.write("\n")
    if colour.palette:
        out.write(render.palette(arguments.amber))
    if colour.sgr:
        out.write(render.AMBER)
    out.write(_run([arguments.eyes]))
    if colour.sgr:
        # Terminated, so the first line of text starts in column one rather than
        # continuing the row the escape was written on.
        out.write(f"{render.RESET}\n")
    out.flush()


def _qr(arguments: argparse.Namespace) -> tuple[str, ...]:
    if not arguments.wifi_uri:
        return ()
    rendered = _run([arguments.qrencode, *QRENCODE_FLAGS, "--", arguments.wifi_uri])
    return tuple(rendered.splitlines())


def _painted() -> str:
    """When this screen was drawn.

    A bare timestamp and nothing about refreshing it: pressing a key here does not
    redraw the banner, it logs the reader in.
    """
    return datetime.now(timezone.utc).strftime("%H:%M UTC")


def _run(command: list[str]) -> str:
    """A generator this screen draws from, or nothing if it cannot be reached.

    Never fatal. A missing QR code is a worse screen; a traceback where the login prompt
    should be is no screen at all.
    """
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout


def _box(arguments: argparse.Namespace) -> Box:
    return Box(
        tag=arguments.tag,
        platform=arguments.platform,
        runs_ai=not arguments.no_ai,
        meets_resource_minimum=not arguments.below_resource_minimum,
        key_guard=KeyGuard(
            action=arguments.key_guard_action,
            grace=arguments.key_guard_grace,
            arm_deadline=arguments.key_guard_arm_deadline,
        ),
        wifi=Wifi(ssid=arguments.wifi_ssid, psk=arguments.wifi_psk),
        portal=Portal(
            host=arguments.portal_host,
            issues_certificates=arguments.portal_issues_certificates,
        ),
    )


def _paths(arguments: argparse.Namespace) -> Paths:
    return Paths(
        network_conf=Path(arguments.network_conf),
        ready_summary=Path(arguments.ready_summary),
        key_guard_state=Path(arguments.key_guard_state),
        key_guard_deadline=Path(arguments.key_guard_deadline),
        recovery_passphrase=Path(arguments.recovery_passphrase),
        portal_password=Path(arguments.portal_password),
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="loom-info",
        description="What this appliance is, and what has to be written down",
    )
    parser.add_argument(
        "--for-issue",
        action="store_true",
        help="render for /run/issue.d, leaving the danger block to its own fragment",
    )

    built = parser.add_argument_group("what the image was built with")
    built.add_argument("--tag", default="")
    built.add_argument("--platform", default="")
    built.add_argument("--amber", default="f7b718")
    built.add_argument("--no-ai", action="store_true")
    built.add_argument("--below-resource-minimum", action="store_true")
    built.add_argument("--key-guard-action", default="poweroff")
    built.add_argument("--key-guard-grace", type=int, default=0)
    built.add_argument("--key-guard-arm-deadline", type=int, default=0)
    built.add_argument("--wifi-ssid", default="")
    built.add_argument("--wifi-psk", default="")
    built.add_argument("--wifi-uri", default="")
    built.add_argument("--portal-host", default="")
    built.add_argument("--portal-issues-certificates", action="store_true")
    built.add_argument(
        "--warning",
        action="append",
        default=[],
        metavar="LINE",
        help="a line of the --debug image's danger block",
    )

    where = parser.add_argument_group("where the live facts are published")
    where.add_argument("--network-conf", default="/etc/loom/network.conf")
    where.add_argument("--ready-summary", default="/run/loom/ready/summary")
    where.add_argument("--key-guard-state", default="/run/loom/key-guard/state")
    where.add_argument("--key-guard-deadline", default="/run/loom/key-guard/deadline")
    where.add_argument("--recovery-passphrase", default="/run/loom/recovery-passphrase")
    where.add_argument("--portal-password", default="/run/loom-portal/password")

    tools = parser.add_argument_group("the generators this screen draws from")
    tools.add_argument("--eyes", default="loom-eyes")
    tools.add_argument("--qrencode", default="qrencode")

    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
