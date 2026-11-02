"""Telling whoever is standing at the box.

The appliance has no remote access, so the console is the only place a message can land.
This mirrors `loom-key-guard`'s `announce`: the journal always, plus `wall` and the
operator's tmux session on a best-effort basis, because there may be no session and no
terminal at all.

Deliberately not /dev/console. `modes.nix` and `network.nix` both explain why -- with no
`console=` on the kernel command line that means the active VT, and it paints over the
operator's session.
"""

import logging
import os
from dataclasses import asdict

from loom_usb_ingest.commands import run_tolerant
from loom_usb_ingest.jsonfile import Formatting, Permissions, write_atomic
from loom_usb_ingest.manifest import Manifest
from loom_usb_ingest.sizes import gib

logger = logging.getLogger(__name__)

_ANNOUNCE_TIMEOUT_S = 10


# How much of a captured error goes in front of the operator. `wall` writes to every
# terminal on the box and tmux's `display-message` is one line over the status bar, so
# a page of mc's JSON or of kubectl's usage would cost somebody the screen they were
# working on. The journal keeps the whole thing either way -- see `failure`.
REASON_LIMIT = 200


def announce(message: str, console_socket: str) -> None:
    """Put one line in front of whoever is at the keyboard."""
    logger.info("%s", message)

    for argv in (
        ["wall", "--nobanner", message],
        # `-l` makes tmux take the argument literally. Without it `display-message`
        # expands its argument as a *format*, and this text is attacker-controlled:
        # `failure` interpolates `condense(detail)`, which comes from `mc mirror
        # --json`'s error message and routinely embeds a filename off the stick, or
        # from mount(8)'s stderr. `#(...)` is parsed but not executed there, so this
        # is not command execution -- what a crafted name buys is garbling the one
        # status-line message the operator sees and reading back `#{session_name}`,
        # `#{pane_current_command}` and `#{socket_path}`. `loom_ready/text.py` knows
        # the same hazard ("No `#`. tmux re-expands ...") and applies it to the
        # other path.
        ["tmux", "-S", console_socket, "display-message", "-l", message],
    ):
        run_tolerant(argv, _ANNOUNCE_TIMEOUT_S)


def condense(detail: str) -> str:
    """One line an operator can act on, out of whatever a tool wrote to stderr.

    The first non-empty line, because every tool this service runs puts the failure
    there and the rest is context: mc follows its error with hints, kubectl with usage.
    """
    for line in (detail or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) > REASON_LIMIT:
            return line[: REASON_LIMIT - 3] + "..."
        return line
    return ""


def failure(headline: str, detail: str, console_socket: str) -> str:
    """Announce something that went wrong, and say what went wrong.

    Without this the operator would get the headline alone -- "not ingested", with the
    reason it was not ingested only in a journal they have no way to read from the
    console session. Whatever a stick does not do, the box says why on the screen.

    The full detail goes to the journal and the condensed line to the console, so the
    journal always shows both what happened and what the operator was told about it.
    Returns the reason, for the caller that also wants it in the pane.
    """
    reason = condense(detail)
    if detail:
        logger.error("%s: %s", headline, detail)
    else:
        logger.error("%s", headline)

    announce(f"[loom] {headline}{f': {reason}' if reason else '.'}", console_socket)
    return reason


def write_state(state_dir: str, state: Manifest) -> None:
    """Publish what the service is doing, for `loom-usb-ingest status`.

    Indented and key-sorted, unlike the progress records: this one is read by people.
    See `jsonfile.write_atomic` for why it goes through a temporary file.
    """
    try:
        write_atomic(
            os.path.join(state_dir, "state.json"),
            asdict(state),
            Permissions(directory=0o700, file=0o600),
            Formatting(indent=2, sort_keys=True, trailing_newline=True),
        )
    except OSError as error:
        logger.warning("Could not write ingest state: %s", error)


def free_bytes(path: str) -> int:
    try:
        stats = os.statvfs(path)
    except OSError:
        return 0
    return stats.f_bavail * stats.f_frsize


# Every ingested byte is stored twice: once in the intake bucket, which nothing
# ever empties automatically, and again in file storage once it is indexed. This
# is the headroom below which that stops being survivable.
HEADROOM_FACTOR = 2.2


def warn_if_short_on_space(root: str, incoming_bytes: int, console_socket: str) -> bool:
    """Warn -- but never refuse -- when the encrypted root is running out.

    Refusing is deliberately not an option: an operator who plugs a stick in
    expects it ingested, and a half-ingested corpus that silently stopped is
    worse than a full disk they were told about. The warning is the whole of the
    mitigation.
    """
    available = free_bytes(root)
    needed = int(incoming_bytes * HEADROOM_FACTOR)
    if available >= needed:
        return False

    announce(
        f"[loom] WARNING: {gib(incoming_bytes)} to ingest needs about "
        f"{gib(needed)} of room (intake plus file storage) and only "
        f"{gib(available)} is free. Ingesting anyway.",
        console_socket,
    )
    return True
