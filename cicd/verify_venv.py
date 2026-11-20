#!/usr/bin/env python3
"""Check that a virtualenv still holds every file its distributions installed.

CI restores `.venv` from a GitLab cache, and a restore can come back short of
files while the runner reports it as a success. Nothing downstream notices:
devenv decides whether to run `poetry install` by comparing the interpreter and
the hashes of `pyproject.toml` and `poetry.lock` against
`.venv/poetry.lock.checksum` -- a file *inside* the virtualenv, and so inside the
restored payload. A virtualenv missing half a package therefore certifies itself
as current, and the job fails much later on an import.

`poetry install` is not a sufficient check on its own, because poetry reads what
is installed from each distribution's `.dist-info` metadata: a distribution that
loses its files but keeps its metadata stays "installed" and is not repaired.

Every installed distribution ships a `RECORD` listing each file it wrote, which
makes the question exact and cheap -- a stat per entry, 0.3s for a full backend
virtualenv. Byte-compilation artifacts are skipped: they are regenerated on
demand, and pip's own `RECORD` lists several hundred `.pyc` paths that are
legitimately absent from a healthy install, so counting them would fail every
virtualenv there is.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

# How many missing files to name before the report says "and N more". A short
# restore loses thousands, and the point of the report is to identify which
# distributions were hit, not to list every file.
DEFAULT_REPORT_LIMIT = 20


@dataclass(frozen=True)
class MissingFile:
    """A path a distribution's `RECORD` claims, which is not on disk."""

    distribution: str
    path: str


@dataclass(frozen=True)
class VerificationResult:
    """What a walk of a virtualenv's `RECORD` files found."""

    checked: int
    distributions: int
    missing: tuple[MissingFile, ...]

    @property
    def complete(self) -> bool:
        """Whether every file every distribution claims is present."""
        return not self.missing


def is_compiled(record_path: str) -> bool:
    """Whether a `RECORD` entry is a byte-compilation artifact.

    These are absent from a healthy virtualenv as often as not: they are written
    on first import rather than by the installer, they move between the path in
    the wheel and `__pycache__/`, and nothing breaks when they are missing.
    """
    if record_path.endswith((".pyc", ".pyo")):
        return True
    return "__pycache__" in record_path.split("/")


def site_packages_of(venv: Path) -> list[Path]:
    """Every `site-packages` directory in a virtualenv."""
    return sorted(venv.glob("lib/python*/site-packages"))


def verify(venv: Path) -> VerificationResult:
    """Check every file every installed distribution claims to have written."""
    checked = 0
    distributions = 0
    missing: list[MissingFile] = []

    for site_packages in site_packages_of(venv):
        for dist_info in sorted(site_packages.glob("*.dist-info")):
            distributions += 1
            record = dist_info / "RECORD"
            try:
                lines = record.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                # A distribution whose own inventory cannot be read is damaged
                # in exactly the way this check exists to catch.
                missing.append(MissingFile(dist_info.name, record.name))
                continue

            for row in csv.reader(lines):
                if not row or not row[0] or is_compiled(row[0]):
                    continue
                checked += 1
                if not (site_packages / row[0]).exists():
                    missing.append(MissingFile(dist_info.name, row[0]))

    return VerificationResult(
        checked=checked, distributions=distributions, missing=tuple(missing)
    )


def report(result: VerificationResult, limit: int) -> None:
    """Say how much is gone, and name enough of it to see the shape."""
    hit = {entry.distribution for entry in result.missing}
    print(
        f"[!] {len(result.missing)} of {result.checked} files are missing, "
        f"across {len(hit)} of {result.distributions} distributions",
        file=sys.stderr,
    )
    for entry in result.missing[:limit]:
        print(f"[!]   {entry.distribution}: {entry.path}", file=sys.stderr)
    if len(result.missing) > limit:
        print(f"[!]   ... and {len(result.missing) - limit} more", file=sys.stderr)


def main() -> int:
    """Verify a virtualenv and report whether it is intact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv", type=Path, default=Path(".venv"), help="the virtualenv to check"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_REPORT_LIMIT,
        help="how many missing files to name",
    )
    args = parser.parse_args()

    if not args.venv.is_dir():
        # Nothing to verify, and nothing wrong: whatever runs next creates it.
        print(f"[*] No virtualenv at {args.venv}")
        return 0

    result = verify(args.venv)
    if not result.distributions:
        # A virtualenv that exists with nothing installed in it is as unusable
        # as one missing files, and vacuously passes the check below.
        print(f"[!] {args.venv} has no installed distributions", file=sys.stderr)
        return 1

    if not result.complete:
        report(result, args.limit)
        return 1

    print(
        f"[*] {args.venv} is intact: {result.checked} files "
        f"across {result.distributions} distributions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
