"""The provenance record: which stick this was, and what came off it.

Written next to the data in the intake bucket, and again into the service's state
directory. It is the only thing that later ties a document in Loom back to the piece of
media it was carried in on, so it is a declared shape rather than a dictionary assembled
at the call site -- the same treatment `progress.py` gives the structurally identical
document it publishes for the console pane, down to the nesting: a record of this many
fields is a handful of smaller records, and each of them is a thing with a name.

The volume rows travel: they are built before a single volume is mounted (for `--dry-
run`), annotated with what happened to each one as the copy goes, and only then
serialised. A renamed key in a dictionary going that far is caught by nothing.
"""

from dataclasses import dataclass, field, replace

__all__ = [
    "KeyGuardRecord",
    "Manifest",
    "Stick",
    "Totals",
    "VolumeMount",
    "VolumeOutcome",
    "VolumePlan",
    "annotate",
]


@dataclass(frozen=True)
class VolumeMount:
    """How a volume would be mounted: which tier it fell in, and on what terms."""

    policy: str
    options: str = ""
    driver: str = ""
    # Why it was refused, or why it is only a generic attempt. Empty for a volume
    # the table knows.
    reason: str = ""


@dataclass(frozen=True)
class VolumeOutcome:
    """What became of it.

    Empty until the copy reaches this volume, and stays empty for `--dry-run`, which
    never mounts anything.
    """

    result: str = ""
    detail: str = ""


@dataclass(frozen=True)
class VolumePlan:
    """One volume of the stick, and where its contents land."""

    device: str
    prefix: str
    fstype: str | None = None
    label: str | None = None
    size_bytes: int = 0
    mount: VolumeMount = field(default_factory=lambda: VolumeMount(policy=""))
    outcome: VolumeOutcome = field(default_factory=VolumeOutcome)


@dataclass(frozen=True)
class Stick:
    """Which piece of media this was, as far as the box could tell."""

    device: str
    name: str
    identifier: str
    size_bytes: int
    # Everything udev reported about it. Kept whole rather than picked over: it is
    # the only record of the device once it has been unplugged.
    udev: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Totals:
    """How much came off it."""

    objects: int = 0
    bytes: int = 0
    failures: int = 0


@dataclass(frozen=True)
class KeyGuardRecord:
    """What the key guard believed while this stick was read.

    Recorded because it is what the exclusion rested on: a box booted on the recovery
    passphrase never arms the guard, and on that box the key stick was told apart by
    partition label alone.
    """

    state: str
    authoritative: bool


@dataclass(frozen=True)
class Manifest:
    """What one device's ingest amounted to."""

    status: str
    prefix: str
    stick: Stick
    key_guard: KeyGuardRecord
    totals: Totals = field(default_factory=Totals)
    volumes: list[VolumePlan] = field(default_factory=list)


def annotate(
    rows: list[VolumePlan], device: str, result: str, detail: str
) -> list[VolumePlan]:
    """Record what became of one volume, leaving the rest of the plan alone."""
    return [
        (
            row
            if row.device != device
            else replace(row, outcome=VolumeOutcome(result=result, detail=detail))
        )
        for row in rows
    ]
