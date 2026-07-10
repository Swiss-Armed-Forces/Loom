import argparse
import sqlite3

from ._db import _print_tree_from_db


def cmd_tree(
    _args: argparse.Namespace,
    *,
    db: sqlite3.Connection,
    cwd: str | None = None,
) -> None:
    _print_tree_from_db(cwd or "", db)
