import fnmatch
import sys
from collections.abc import Iterable

from ._constants import ERR_NO_FILE_FOUND
from ._types import IndexEntry


def resolve_name(
    entries: Iterable[IndexEntry], name: str, *, wildcards: bool = True
) -> list[IndexEntry]:
    exact: list[IndexEntry] = []
    suffix: list[IndexEntry] = []
    prefix: list[IndexEntry] = []
    glob_matches: list[IndexEntry] = []

    for e in entries:
        if e.name == name:
            exact.append(e)
        elif e.name.endswith(name):
            suffix.append(e)
        elif name.endswith("/") and e.name.startswith(name):
            prefix.append(e)
        elif wildcards and fnmatch.fnmatch(e.name, name):
            glob_matches.append(e)

    matches = exact or suffix or prefix or glob_matches

    if not matches:
        print(f"Error: {ERR_NO_FILE_FOUND} '{name}'", file=sys.stderr)
        sys.exit(1)

    return matches
