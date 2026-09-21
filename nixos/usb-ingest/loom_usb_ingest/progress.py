"""What the copy is doing, published where the operator can watch it.

A `mc mirror` of a full stick is minutes to hours, and until now the only sign of it was
two lines from `report.announce` -- one when it started and one when it finished. Anyone
standing at the box had no way to tell a slow copy from a stuck one, and no way to know
when the stick could come out.

So each device keeps a small record here, and `loom-usb-ingest --watch` renders every
record it finds into the pane `pane.py` splits off the console session. Two processes
and a file rather than one process drawing directly, because the ingest runs as root out
of a udev-triggered unit and the pane belongs to the operator's tmux server: they cannot
be the same process, and a file is the whole of what they have to share.

The directory is world-readable, unlike the rest of the service's state (usb-
ingest.nix): the reader is the operator's own session, and what is in here is byte
counts and device paths.
"""

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum

logger = logging.getLogger(__name__)

SUFFIX = ".json"

# The floor on how often a record is rewritten. `mc mirror` reports every object, and
# the pane refreshes once a second: anything faster is writes nobody sees.
MIN_WRITE_INTERVAL_S = 0.5


class Stage(StrEnum):
    """Where one device has got to."""

    WAITING = "waiting"
    COPYING = "copying"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True)
class VolumeProgress:
    """Which volume of the stick is being copied, and which of how many it is."""

    path: str = ""
    index: int = 0
    count: int = 0


@dataclass(frozen=True)
class Counts:
    """How much of it has moved.

    `total` is the bytes on the volume as the filesystem reports them, and is 0 when it
    could not be measured -- which is what makes the bar a pulse rather than a lie.
    """

    total: int = 0
    copied: int = 0
    objects: int = 0
    failures: int = 0


@dataclass(frozen=True)
class DeviceProgress:
    """One device's line in the pane."""

    device: str
    name: str
    stage: Stage = Stage.WAITING
    volume: VolumeProgress = field(default_factory=VolumeProgress)
    counts: Counts = field(default_factory=Counts)
    updated: float = 0.0

    @property
    def finished(self) -> bool:
        return self.stage in (Stage.DONE, Stage.FAILED)


def path_for(progress_dir: str, kernel_name: str) -> str:
    return os.path.join(progress_dir, f"{kernel_name}{SUFFIX}")


def publish(progress_dir: str, kernel_name: str, progress: DeviceProgress) -> None:
    """Write one device's record, atomically.

    Through a temporary file in the same directory so a reader can never catch a
    half-written document -- the same way key-guard.nix writes its own state, and for
    the same reason: the reader is a loop with a one-second period.
    """
    try:
        os.makedirs(progress_dir, mode=0o755, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=progress_dir, delete=False, encoding="utf-8"
        ) as handle:
            json.dump(asdict(progress), handle)
            temporary = handle.name
        os.chmod(temporary, 0o644)
        os.replace(temporary, path_for(progress_dir, kernel_name))
    except OSError as error:
        # Never fatal: this is a display, and the copy it describes matters more.
        logger.warning("Could not publish ingest progress: %s", error)


def withdraw(progress_dir: str, kernel_name: str) -> None:
    """Forget a device, because it has been unplugged."""
    try:
        os.unlink(path_for(progress_dir, kernel_name))
    except OSError:
        pass


def read_all(progress_dir: str) -> list[DeviceProgress]:
    """Every device currently being ingested, oldest record first."""
    records = []
    try:
        names = sorted(os.listdir(progress_dir))
    except OSError:
        return []

    for name in names:
        if not name.endswith(SUFFIX):
            continue
        record = _read(os.path.join(progress_dir, name))
        if record is not None:
            records.append(record)
    return records


def _read(path: str) -> DeviceProgress | None:
    try:
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError):
        return None

    try:
        return DeviceProgress(
            device=str(raw["device"]),
            name=str(raw["name"]),
            stage=Stage(raw["stage"]),
            volume=VolumeProgress(
                path=str(raw["volume"]["path"]),
                index=int(raw["volume"]["index"]),
                count=int(raw["volume"]["count"]),
            ),
            counts=Counts(
                total=int(raw["counts"]["total"]),
                copied=int(raw["counts"]["copied"]),
                objects=int(raw["counts"]["objects"]),
                failures=int(raw["counts"]["failures"]),
            ),
            updated=float(raw["updated"]),
        )
    except (KeyError, TypeError, ValueError):
        # A record written by a different version of this program. Dropping it costs
        # one line in the pane; refusing to read any would cost the whole display.
        return None


class Reporter:
    """The writing half, held by the ingest for the life of one device.

    Keeps the record it last published and replaces it, rather than a field per
    number: what goes to disk and what is held in memory are then the same thing, and
    there is one place a new field has to be added.
    """

    def __init__(self, progress_dir: str, kernel_name: str, device: str, name: str):
        self._dir = progress_dir
        self._kernel_name = kernel_name
        self._record = DeviceProgress(device=device, name=name)
        # Rate-limited: `mc mirror` reports every object, and a stick of small files
        # would otherwise be one write per file.
        self._last_write = 0.0
        self.update(force=True)

    @property
    def stage(self) -> Stage:
        return self._record.stage

    def start_volume(self, volume: str, index: int, count: int, total: int) -> None:
        """Begin one volume, carrying the object count from the ones before it."""
        self._record = replace(
            self._record,
            stage=Stage.COPYING,
            volume=VolumeProgress(path=volume, index=index, count=count),
            counts=replace(self._record.counts, total=total, copied=0),
        )
        self.update(force=True)

    def advance(self, objects: int, copied: int) -> None:
        """One `mc mirror` event: totals for the volume in flight."""
        self._record = replace(
            self._record,
            counts=replace(self._record.counts, objects=objects, copied=copied),
        )
        self.update()

    def finish(self, objects: int, failures: int) -> None:
        """The copy is over, one way or the other."""
        self._record = replace(
            self._record,
            stage=Stage.FAILED if failures else Stage.DONE,
            counts=replace(self._record.counts, objects=objects, failures=failures),
        )
        self.update(force=True)

    def update(self, force: bool = False) -> None:
        """Publish, unless the last write was too recent to be worth another."""
        now = time.time()
        if not force and now - self._last_write < MIN_WRITE_INTERVAL_S:
            return
        self._last_write = now
        publish(self._dir, self._kernel_name, replace(self._record, updated=now))


def volume_bytes(mountpoint: str) -> int:
    """How much data is on a mounted volume, as the filesystem reports it.

    `statvfs` rather than a walk: a 2 TB stick of small files would cost minutes to
    measure and the answer would be no better. 0 when the filesystem will not say, which
    the display treats as "no total" rather than as "nothing to copy".
    """
    try:
        stats = os.statvfs(mountpoint)
    except OSError:
        return 0
    return (stats.f_blocks - stats.f_bfree) * stats.f_frsize
