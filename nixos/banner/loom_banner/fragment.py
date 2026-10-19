"""`loom-issue-fragment`: the blocks that land under the banner.

Four units have something to add to the login screen after `loom-info` has already
rendered it -- a wired port that does not exist, an access point that never came up,
the warning a --debug image owes whoever walks past, and the portal's daily password.
agetty reads `/run/issue.d` in filename order, so each writes a numbered file and the
number is the position on screen.

Two rules come with that, and they are the reason this is one program rather than a
`printf` in each unit:

  * **Written through a temporary file and renamed.** A getty respawning mid-write
    must never paint half a message, and the one whose message is half a passphrase
    is the one that matters.
  * **The screen gets colour; the journal does not.** Each unit also logs what it
    wrote, and SGR escapes in `journalctl` output help nobody.
"""

import argparse
import os
import sys
import tempfile
from io import StringIO
from pathlib import Path

from loom_banner import render

# Where agetty is pointed, as the getty wrapper spells it.
DEFAULT_DIR = Path("/run/issue.d")

# What the two kinds of block are titled. One word each, because the lines under
# them are the message and the rule is only what makes them findable.
#
# They are told apart because the screen says both kinds of thing: a wired port that
# does not exist is wrong and wants the eye, a port claimed automatically is merely
# worth knowing. Rendering the second in red would make a working box look broken.
PROBLEM_TITLE = "Problem"
NOTICE_TITLE = "Notice"


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv if argv is not None else sys.argv[1:])
    if not (arguments.warn or arguments.note or arguments.bar):
        # Nothing to say writes nothing at all, rather than an empty file that costs
        # the screen a blank row.
        return 0

    for_screen = _render(arguments, colour=True)
    for_journal = _render(arguments, colour=False)

    path = Path(arguments.dir) / f"{arguments.name}.issue"
    _publish(path, for_screen)
    sys.stdout.write(for_journal)
    return 0


def _render(arguments: argparse.Namespace, colour: bool) -> str:
    stream = StringIO()
    console = render.console(stream, render.Colour(sgr=colour, palette=False))
    if arguments.warn:
        console.print(render.rule(PROBLEM_TITLE, style=render.PROBLEM_STYLE))
        for line in arguments.warn:
            console.print(render.note(line))
    if arguments.note:
        console.print(render.rule(NOTICE_TITLE))
        for line in arguments.note:
            console.print(render.note(line))
    if arguments.bar:
        for line in render.danger(arguments.bar):
            console.print(line)
    return stream.getvalue()


def _publish(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    )
    try:
        with handle:
            handle.write(content)
        # Readable by agetty, which is root, and by anybody who wants to see what the
        # screen says -- it is on a monitor in the room either way.
        os.chmod(handle.name, 0o644)
        os.replace(handle.name, path)
    except OSError:
        Path(handle.name).unlink(missing_ok=True)
        raise


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="loom-issue-fragment",
        description="Write a block of the appliance login screen",
    )
    parser.add_argument(
        "name",
        help="the fragment's name without its suffix, whose number is its position",
    )
    parser.add_argument(
        "--warn",
        action="append",
        default=[],
        metavar="LINE",
        help="a line of a problem block, under a red rule",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        metavar="LINE",
        help="a line of a notice block, under a plain rule",
    )
    parser.add_argument(
        "--bar",
        action="append",
        default=[],
        metavar="LINE",
        help="a line of a danger block, white on red",
    )
    parser.add_argument(
        "--dir",
        default=str(DEFAULT_DIR),
        help=f"where to write it (default {DEFAULT_DIR})",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
