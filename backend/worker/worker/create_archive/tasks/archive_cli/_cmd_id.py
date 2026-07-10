import argparse
import sqlite3
import sys

from ._constants import FILES_DIR
from ._db import get_storage_results
from ._utils import _vpath


def cmd_id(
    args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    cwd: str | None = None,
) -> None:
    file_ref = args.file_ref
    if file_ref.startswith(f"{FILES_DIR}/"):
        storage_id = file_ref[len(f"{FILES_DIR}/") :]
    else:
        storage_id = file_ref

    results = get_storage_results(db, storage_id)

    if cwd:
        results = [r for r in results if _vpath(r.name).startswith(cwd + "/")]

    if not results:
        print(f"Error: no file found with id '{storage_id}'", file=sys.stderr)
        sys.exit(1)

    for name, role in results:
        if role == "file":
            print(name)
        else:
            print(f"{name} ({role})")
