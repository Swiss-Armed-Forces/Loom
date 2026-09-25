"""What the box's disks are, and which of them may be written to.

The device interlock is the most important thing in this package: it is what keeps the
installer from eating the USB stick it is running from, or a disk somebody cares about.
Everything here is asked through a `CommandRunner` rather than through `subprocess`
directly, so the rules can be exercised against recorded answers -- see
tests/test_devices.py.
"""

import os
import re
from dataclasses import dataclass
from enum import StrEnum

from loom_installer import constants
from loom_installer.commands import CommandRunner

# What `_whole_disks` asks. A constant rather than a literal inside the function
# because the test answers this exact command -- a fake box is only as good as the
# questions it was given.
LSBLK_WHOLE_DISKS = [
    "lsblk",
    "--nodeps",
    "--noheadings",
    "--raw",
    "--paths",
    "--output",
    "NAME,TYPE",
]

# The backstop under every other check below: USB mass storage enumerates as sd*, so
# a stick can never end up in the target list even if all of them were to break.
NVME_NAMESPACE = re.compile(r"^/dev/nvme[0-9]+n[0-9]+$")


class KeyState(StrEnum):
    """What the stick's key partition holds."""

    PRESENT = "present"
    EMPTY = "empty"
    MISSING = "missing"


@dataclass(frozen=True)
class Disk:
    """One whole disk, as the operator will see it named."""

    path: str
    model: str
    serial: str
    size: str

    def describe(self) -> str:
        return f"{self.path}  {self.model}  SN {self.serial}  {self.size}"


def parent_of(runner: CommandRunner, partition: str) -> str:
    """Parent disk of a partition, e.g. /dev/nvme0n1p1 -> /dev/nvme0n1."""
    listing = runner.output(
        ["lsblk", "--noheadings", "--raw", "--paths", "--output", "PKNAME", partition]
    )
    return listing.strip().splitlines()[0].strip() if listing.strip() else ""


def sysfs_attr(runner: CommandRunner, disk: str, attr: str) -> str:
    """One /sys/block/<disk>/device/<attr>, trimmed, or "unknown".

    NVMe pads the Identify Controller fields to a fixed width with spaces, so a serial
    arrives as "S6XSNU0T12345       ". Every consumer of this is a line on the
    operator's screen -- the menu's status block, the disk list in the destructive
    interlock -- where padding pushes the columns apart and reads as a truncated value.
    """
    value = runner.read_text(f"/sys/block/{os.path.basename(disk)}/device/{attr}")
    if value is None:
        return "unknown"
    return value.strip() or "unknown"


def describe_disk(runner: CommandRunner, disk: str) -> Disk:
    size = runner.output(
        ["lsblk", "--nodeps", "--noheadings", "--raw", "--output", "SIZE", disk]
    ).strip()
    return Disk(
        path=disk,
        model=sysfs_attr(runner, disk, "model"),
        serial=sysfs_attr(runner, disk, "serial"),
        size=size or "unknown",
    )


def boot_disk(runner: CommandRunner) -> str | None:
    """The disk we booted from, resolved from our own partition labels.

    Returns None when the boot medium is ambiguous -- with a second Loom stick attached
    the labels resolve to two disks, and guessing would be how the wrong device gets
    erased. Every caller treats that as fatal.
    """
    disks = set()
    for label in (
        constants.KEY_LABEL,
        constants.LIVE_STORE_LABEL,
        constants.LIVE_ESP_LABEL,
    ):
        partition = runner.resolve(f"{constants.BY_PARTLABEL}/{label}")
        if partition is None or not runner.is_block_device(partition):
            continue
        parent = parent_of(runner, partition)
        if parent:
            disks.add(parent)

    if len(disks) != 1:
        return None
    return disks.pop()


def target_disks(runner: CommandRunner) -> list[str]:
    """Internal NVMe namespaces only, minus the boot medium.

    Minus anything removable, on the USB bus, or currently mounted as well -- anything
    with a mounted partition is the live system, not a target.

    Sorted, because the order is load-bearing: every disk here joins the pool, and the
    first one gets the ESP and the NVRAM boot entry. lsblk already lists in kernel
    order, but "already" is not a guarantee to hang a boot partition on.
    """
    boot = boot_disk(runner)
    if boot is None:
        return []

    targets = []
    for disk in _whole_disks(runner):
        if disk == boot:
            continue
        if not NVME_NAMESPACE.match(disk):
            continue
        if _is_removable(runner, disk):
            continue
        if _is_usb(runner, disk):
            continue
        if _has_mounted_partition(runner, disk):
            continue
        targets.append(disk)

    return sorted(targets)


def _whole_disks(runner: CommandRunner) -> list[str]:
    listing = runner.output(LSBLK_WHOLE_DISKS)
    disks = []
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "disk":
            disks.append(fields[0])
    return disks


def _is_removable(runner: CommandRunner, disk: str) -> bool:
    """Unreadable counts as removable: the point is to refuse when unsure."""
    value = runner.read_text(f"/sys/block/{os.path.basename(disk)}/removable")
    return value is None or value.strip() == "1"


def _is_usb(runner: CommandRunner, disk: str) -> bool:
    properties = runner.output(
        ["udevadm", "info", "--query=property", f"--name={disk}"]
    )
    return any(line.strip() == "ID_BUS=usb" for line in properties.splitlines())


def _has_mounted_partition(runner: CommandRunner, disk: str) -> bool:
    mountpoints = runner.output(
        ["lsblk", "--noheadings", "--raw", "--paths", "--output", "MOUNTPOINTS", disk]
    )
    return any(line.strip() for line in mountpoints.splitlines())


def key_state(runner: CommandRunner, key_device: str, locked: bool) -> KeyState:
    """What the stick's key partition holds.

    A stick that was never provisioned would install fine and then never boot, so this
    is checked before anything destructive happens.

    Compared against /dev/zero by `cmp` rather than read here: the partition is 4096
    bytes of binary, and the answer wanted is one bit.

    On a `--lock-key` stick those bytes are a LUKS2 header rather than the key, and
    "not zeroes" stops being enough -- a partition holding anything at all would pass.
    So `PRESENT` there means cryptsetup recognises a container. The zero check still
    runs first either way, because an unprovisioned partition is the one failure this
    exists to name precisely: `EMPTY` sends the operator to `--flash`, where
    `MISSING` would send them looking for a stick that is already plugged in.

    `locked` is passed in rather than read off `settings()` here, so that nothing in
    this module depends on what the environment says -- every rule in it is answered
    through the runner, which is what lets tests/test_disk_selection.py exercise them
    against recorded answers.
    """
    if not runner.is_block_device(key_device):
        return KeyState.MISSING

    zeroed = runner.run(
        ["cmp", "--quiet", f"--bytes={constants.KEY_BYTES}", key_device, "/dev/zero"]
    )
    if zeroed.ok:
        return KeyState.EMPTY

    if locked and not is_key_container(runner, key_device):
        return KeyState.EMPTY

    return KeyState.PRESENT


def is_key_container(runner: CommandRunner, key_device: str) -> bool:
    """Whether the key partition holds a LUKS2 container rather than the key itself.

    `--type luks2` rather than a bare `isLuks`: LUKS1 would answer yes, and a LUKS1
    container here is not something this ever writes, so it is a stick from somewhere
    else rather than one of ours.
    """
    return runner.run(["cryptsetup", "isLuks", "--type", "luks2", key_device]).ok


def pool_bytes(runner: CommandRunner, disks: list[str]) -> int:
    """Total capacity of the disks that would be pooled."""
    total = 0
    for disk in disks:
        size = runner.output(["blockdev", "--getsize64", disk]).strip()
        try:
            total += int(size)
        except ValueError:
            continue
    return total
