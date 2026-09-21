"""The pane the copy is watched in.

The console session (console.nix) is three panes: the bring-up log turned k9s, btop
beside it, and the assistant underneath. While a stick is being copied the k9s pane
is split again, horizontally -- k9s stays on top, the copy is drawn below it -- and
when the last stick has been unplugged the split is undone and k9s has the space
back.

Two rules shape the whole module, and both come from where it runs:

  * It is never an error for any of this to fail. The ingest is started by a udev
    rule and may well run on a box where nobody has opened a session at all, so
    every tmux call here is best-effort and the copy is unaffected by all of them.
  * The pane it splits is found by the `@loom-main` option console.nix sets on it,
    not by index. Indices follow layout position and are rewritten by every split --
    including this one.
"""

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

TMUX_TIMEOUT_S = 10

# Which pane to split, and what to mark the new one with so it can be found again.
MAIN_PANE_OPTION = "@loom-main"
INGEST_PANE_OPTION = "@loom-usb"

# k9s keeps the larger half: it is the pane an operator watches on this box, and the
# copy below it is four lines of text however much room it is given.
INGEST_PANE_PERCENT = 35


def _tmux(socket: str, *arguments: str) -> str | None:
    """One tmux command against the operator's server, or None if it did not run."""
    try:
        completed = subprocess.run(
            ["tmux", "-S", socket, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=TMUX_TIMEOUT_S,
        )
    except (subprocess.SubprocessError, OSError) as error:
        logger.debug("tmux %s: %s", arguments, error)
        return None
    if completed.returncode != 0:
        logger.debug("tmux %s: %s", arguments, completed.stderr.strip())
        return None
    return completed.stdout.strip()


def _pane_with(socket: str, option: str) -> str | None:
    listing = _tmux(
        socket, "list-panes", "-t", "loom", "-F", f"#{{pane_id}} #{{{option}}}"
    )
    if not listing:
        return None
    for line in listing.splitlines():
        pane_id, _, value = line.partition(" ")
        if value.strip():
            return pane_id
    return None


def open_pane(socket: str, command: list[str]) -> str | None:
    """Split the k9s pane and run `command` in the lower half.

    Idempotent: a second stick plugged in while the first is still copying finds the
    pane already there and shares it, because the watcher renders every device it
    finds rather than one.
    """
    existing = _pane_with(socket, INGEST_PANE_OPTION)
    if existing is not None:
        return existing

    main = _pane_with(socket, MAIN_PANE_OPTION)
    if main is None:
        logger.info("No console session to draw ingest progress in")
        return None

    pane = _tmux(
        socket,
        "split-window",
        "-v",
        "-l",
        f"{INGEST_PANE_PERCENT}%",
        "-t",
        main,
        "-P",
        "-F",
        "#{pane_id}",
        *command,
    )
    if pane is None:
        return None

    _tmux(socket, "set-option", "-p", "-t", pane, INGEST_PANE_OPTION, "1")
    # A split leaves the new pane active, and the operator may be typing in the
    # assistant: a copy starting under their hands must not take the keyboard away.
    _tmux(socket, "select-pane", "-t", main)
    return pane


def close_pane(socket: str) -> None:
    """Undo the split, giving k9s its space back."""
    pane = _pane_with(socket, INGEST_PANE_OPTION)
    if pane is None:
        return
    _tmux(socket, "kill-pane", "-t", pane)


def watcher_command(progress_dir: str, console_socket: str) -> list[str]:
    """How the pane re-enters this program to draw.

    `sys.argv[0]` rather than the name on PATH: the pane is spawned by the tmux server,
    which runs as the operator and has no reason to have the ingest on its PATH at all.
    """
    return [
        os.path.realpath(sys.argv[0]),
        "--watch",
        "--progress-dir",
        progress_dir,
        "--console-socket",
        console_socket,
    ]
