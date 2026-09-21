"""Telling whoever is standing at the box.

The appliance has no remote access, so the console is the only place a message can land.
This mirrors `loom-key-guard`'s `announce`: the journal always, plus `wall` and the
operator's tmux session on a best-effort basis, because there may be no session and no
terminal at all.

Deliberately not /dev/console. `modes.nix` and `network.nix` both explain why -- with no
`console=` on the kernel command line that means the active VT, and it paints over the
operator's session.
"""

import json
import logging
import os
import subprocess
import tempfile

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
        ["tmux", "-S", console_socket, "display-message", message],
    ):
        try:
            subprocess.run(
                argv, check=False, capture_output=True, timeout=_ANNOUNCE_TIMEOUT_S
            )
        except (subprocess.SubprocessError, OSError):
            continue


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

    Without this the operator got the headline alone -- "not ingested", with the reason
    it was not ingested only in a journal they have no way to read from the console
    session. Whatever a stick does not do, the box now says why on the screen.

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


def write_state(state_dir: str, state: dict) -> None:
    """Publish what the service is doing, for `loom-usb-ingest status`.

    Written through a temporary file in the same directory so a reader can never catch a
    half-written document, the same way key-guard.nix writes its own state.
    """
    os.makedirs(state_dir, mode=0o700, exist_ok=True)
    path = os.path.join(state_dir, "state.json")

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=state_dir, delete=False, encoding="utf-8"
        ) as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary = handle.name
        os.replace(temporary, path)
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
        f"[loom] WARNING: {_gib(incoming_bytes)} to ingest needs about "
        f"{_gib(needed)} of room (intake plus file storage) and only "
        f"{_gib(available)} is free. Ingesting anyway.",
        console_socket,
    )
    return True


def _gib(value: int) -> str:
    return f"{value / (1024 ** 3):.1f} GiB"
