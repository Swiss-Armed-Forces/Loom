"""Which block devices may be ingested, and which must never be touched.

The one that must never be touched is the LUKS key stick. `nixos/key-guard.nix`
polls it every two seconds and powers the box off ten seconds after it stops
reading, so disturbing it is not a cosmetic mistake.

Identifying it by `/dev/disk/by-partlabel/loom-key` is not good enough, and
key-guard.nix says why in its own comments: that path is not unique, and with a
second Loom stick attached udev points it at whichever was linked last. The
authoritative answer is the guard's own `device` file, which holds the node it
armed on -- and it got there by proving, with `cryptsetup --test-passphrase`,
that the stick actually unlocks *this* disk.
"""

import json
import os.path
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum

# Every partition label the appliance itself uses: the stick's, and the internal
# disk's. installer-scripts/common.sh owns these names.
LOOM_PARTLABELS: frozenset[str] = frozenset(
    {
        "loom-key",
        "loom-esp",
        "loom-root-luks",
        "loom-live-esp",
        "loom-live-store",
    }
)


class GuardState(StrEnum):
    ARMED = "armed"
    IDLE = "idle"
    DISARMED = "disarmed"
    TRIPPED = "tripped"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class KeyGuard:
    """What the key guard currently believes, as read from its state directory."""

    state: GuardState
    disk: str | None
    """Kernel name of the whole disk holding the key, e.g. `sdb`."""

    @property
    def authoritative(self) -> bool:
        """True when the guard has positively identified the key stick.

        When it has not -- a box booted on the recovery passphrase leaves the
        guard idle -- there is no proven key device, and exclusion falls back to
        partition labels, which is weaker.
        """
        return self.state is GuardState.ARMED and self.disk is not None


@dataclass(frozen=True)
class Volume:
    path: str
    fstype: str | None
    label: str | None
    partlabel: str | None
    size: int
    mountpoint: str | None


@dataclass(frozen=True)
class Disk:
    path: str
    kernel_name: str
    size: int
    volumes: tuple[Volume, ...] = field(default_factory=tuple)
    properties: dict[str, str] = field(default_factory=dict)

    @property
    def partlabels(self) -> frozenset[str]:
        return frozenset(v.partlabel for v in self.volumes if v.partlabel)


@dataclass(frozen=True)
class Verdict:
    ingest: bool
    reason: str


def classify_disk(
    disk: Disk,
    guard: KeyGuard,
    protected_disks: frozenset[str],
) -> Verdict:
    """Decide whether a whole disk may be ingested.

    `protected_disks` are the kernel names carrying `/` and `/boot`. They are
    passed in rather than looked up here so that the decision stays a pure
    function of what was observed.
    """
    if disk.kernel_name in protected_disks:
        return Verdict(False, "carries the appliance's own root or boot filesystem")

    if guard.disk is not None and disk.kernel_name == guard.disk:
        return Verdict(False, "is the LUKS key stick the key guard armed on")

    # Belt and braces, and the only line of defence when the guard is idle: any
    # disk carrying an appliance partition label is Loom's own media. Catches
    # the installer stick, whose `loom-live-store` partition holds ~60 GB of
    # container images nobody wants indexed, and another box's key stick.
    shared = disk.partlabels & LOOM_PARTLABELS
    if shared:
        return Verdict(False, f"carries Loom partition labels ({', '.join(sorted(shared))})")

    if all(volume.mountpoint for volume in disk.volumes) and disk.volumes:
        return Verdict(False, "every volume on it is already mounted")

    return Verdict(True, "")


def read_key_guard(state_dir: str) -> KeyGuard:
    """Read the guard's state and resolve its device to a whole disk."""
    state = _read_text(f"{state_dir}/state") or ""
    device = _read_text(f"{state_dir}/device")

    try:
        parsed = GuardState(state.strip())
    except ValueError:
        parsed = GuardState.UNKNOWN

    return KeyGuard(state=parsed, disk=parent_disk(device) if device else None)


def _read_text(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def _run(argv: list[str]) -> str:
    return subprocess.run(
        argv, check=True, capture_output=True, text=True, timeout=60
    ).stdout


def parent_disk(device: str) -> str | None:
    """Map a partition node to the kernel name of the disk containing it.

    A device that is already a whole disk maps to itself, which is what makes
    this safe to call on the guard's node without knowing which it is.
    """
    # `--nodeps` is what makes this a question about one device: without it
    # lsblk prints the whole subtree, and the first row is not reliably the one
    # asked about -- for a disk carrying a dm-crypt mapping it is the holder.
    # With it there is exactly one row: "PKNAME KNAME" for a partition, and
    # "KNAME" alone for anything with no parent, which is the disk mapping to
    # itself.
    try:
        output = _run(
            ["lsblk", "--nodeps", "--noheadings", "--output", "PKNAME,KNAME", device]
        )
    except (subprocess.SubprocessError, OSError):
        return None

    for line in output.splitlines():
        fields = line.split()
        if not fields:
            continue
        return fields[0]
    return None


def protected_disks() -> frozenset[str]:
    """Kernel names of the disks carrying the appliance's own root and boot."""
    found = set()
    for mountpoint in ("/", "/boot", "/nix/store"):
        try:
            source = _run(
                ["findmnt", "--noheadings", "--output", "SOURCE", "--target", mountpoint]
            ).strip()
        except (subprocess.SubprocessError, OSError):
            continue
        if not source.startswith("/dev/"):
            continue
        # A dm-crypt mapping resolves through its slave to the real disk.
        disk = parent_disk(source)
        if disk:
            found.add(disk)
            continue
    return frozenset(found)


def udev_properties(device: str) -> dict[str, str]:
    try:
        output = _run(["udevadm", "info", "--query=property", "--name", device])
    except (subprocess.SubprocessError, OSError):
        return {}

    properties = {}
    for line in output.splitlines():
        key, _, value = line.partition("=")
        if key and value:
            properties[key] = value
    return properties


def _node_for(nodes: list[dict], device: str) -> dict:
    name = os.path.basename(device)
    for node in nodes:
        if node.get("path") == device or os.path.basename(node.get("kname") or "") == name:
            return node
    return nodes[0] if nodes else {}


def _volume_from(entry: dict) -> Volume:
    return Volume(
        path=entry.get("path", ""),
        fstype=entry.get("fstype"),
        label=entry.get("label"),
        partlabel=entry.get("partlabel"),
        size=int(entry.get("size") or 0),
        mountpoint=entry.get("mountpoint"),
    )


def inspect_disk(device: str) -> Disk:
    """Build the full picture of a disk: its volumes and its udev identity.

    A disk with no partition table but a filesystem of its own -- the
    "superfloppy" layout most cameras and many SD cards use -- is reported by
    lsblk as a single node with an fstype and no children, and is treated here as
    one volume covering the whole device.
    """
    # Two flags this call cannot do without, both learned the hard way:
    #
    #   * `--tree`, because `--json` alone lists a disk and its partitions as
    #     siblings (util-linux 2.42). Without it `children` is never there, a
    #     partitioned stick looks like a disk with no volumes at all, and a disk
    #     carrying `loom-live-store` is ingested rather than skipped -- the
    #     partition label the exclusion reads is on a partition this never saw.
    #   * No `--paths`, because it rewrites *every* name column as a full path,
    #     KNAME included. A `kernel_name` of "/dev/sdb" matches neither the bare
    #     name `parent_disk` resolves the key stick and the root disk to -- so
    #     both exclusions in `classify_disk` stop matching -- nor `os.path.join`,
    #     which discards everything before an absolute component when the
    #     mountpoint is built. PATH is a full path either way, which is all that
    #     was wanted from it.
    output = _run(
        [
            "lsblk",
            "--json",
            "--tree",
            "--bytes",
            "--output",
            "PATH,KNAME,TYPE,FSTYPE,LABEL,PARTLABEL,SIZE,MOUNTPOINT",
            device,
        ]
    )
    return disk_from_lsblk(
        json.loads(output)["blockdevices"],
        device,
        udev_properties(device),
    )


def disk_from_lsblk(nodes: list[dict], device: str, properties: dict[str, str]) -> Disk:
    """Build a `Disk` from lsblk's `blockdevices`. Split out so it can be tested.

    The node asked about is found by name rather than taken as the first one:
    lsblk puts holders ahead of the device they hold, so a disk carrying a
    dm-crypt mapping is not the head of its own listing.
    """
    root = _node_for(nodes, device)

    children = root.get("children") or []
    volumes = (
        tuple(_volume_from(child) for child in children)
        if children
        else ((_volume_from(root),) if root.get("fstype") else ())
    )

    return Disk(
        path=root.get("path", device),
        # Bare, never a path: `classify_disk` compares it against what
        # `parent_disk` resolves the key stick and the root disk to, and
        # `__main__` joins it onto the mount root. `basename` rather than trust,
        # because which lsblk flags are in play is not this function's business.
        kernel_name=os.path.basename(root.get("kname") or ""),
        size=int(root.get("size") or 0),
        volumes=volumes,
        properties=properties,
    )
