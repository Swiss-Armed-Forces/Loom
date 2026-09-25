"""Writing a JSON document where a reader may be looking at it already.

Both documents this service publishes -- the progress record the console pane reads once
a second, and the state file `loom-usb-ingest status` reads -- are written the same way
key-guard.nix writes its own state: into a temporary file in the target directory, then
renamed over the old one. `os.replace` is atomic within a filesystem, so a reader sees
either the previous document or the new one and never half of either.

One helper rather than the routine written once per module, so the cleanup on the error
path only has to be right in one place.
"""

import json
import os
import tempfile
from dataclasses import dataclass

__all__ = ["Formatting", "Permissions", "COMPACT", "write_atomic"]


@dataclass(frozen=True)
class Permissions:
    """Who may read what is written.

    Two modes rather than one because the callers disagree: the progress directory is
    world-readable so that the operator's own tmux session can draw it, while the
    state directory is root-only.
    """

    directory: int
    file: int


@dataclass(frozen=True)
class Formatting:
    """How the document is laid out.

    Indented and key-sorted for the state file, which is read by people, and compact for
    the progress records, which are rewritten twice a second.
    """

    indent: int | None = None
    sort_keys: bool = False
    trailing_newline: bool = False


# The default for `write_atomic`, as a value rather than a call in the signature --
# the same reason `transfer.NO_HOOKS` is one. Shared safely because it is frozen.
COMPACT = Formatting()


def write_atomic(
    path: str,
    document: object,
    permissions: Permissions,
    formatting: Formatting = COMPACT,
) -> None:
    """Serialise `document` to `path`, atomically.

    Raises OSError, like `open`.
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, mode=permissions.directory, exist_ok=True)

    temporary = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directory, delete=False, encoding="utf-8"
        ) as handle:
            temporary = handle.name
            json.dump(
                document,
                handle,
                indent=formatting.indent,
                sort_keys=formatting.sort_keys,
            )
            if formatting.trailing_newline:
                handle.write("\n")
        os.chmod(temporary, permissions.file)
        os.replace(temporary, path)
        temporary = ""
    finally:
        # A half-written document must not be left behind in the directory a sweep
        # reads: `read_all` would find it, fail to parse it, and leave it there for
        # every subsequent sweep to trip over.
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
