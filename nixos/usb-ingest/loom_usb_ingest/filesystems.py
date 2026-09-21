"""What to mount a volume with, and whether to mount it at all.

Three tiers, in order:

- Refused outright. Container formats that need a key or an assembly step we
  have no business performing on someone else's media.
- The table. A known filesystem, an explicit driver and explicit options.
- Best effort. Anything else the running kernel says it supports is attempted
  with `mount -t auto` and the baseline options only, so coverage is not capped
  by what this table happens to list.

Why not simply `mount -t auto` throughout? It probes with libblkid and mounts
the type it identified, so it detects no worse -- but it then discards the type,
and the type is exactly what the options below are keyed on. It would also pick
the NTFS driver by whichever mount helper happens to be installed rather than by
our choice of FUSE, cannot reach a FUSE driver that ships no `mount.<type>`
helper at all, and cannot refuse anything or say why.
"""

from dataclasses import dataclass
from enum import StrEnum

# Applied to every mount, in every tier.
#
# `ro` is the headline, but it is not sufficient on its own -- see JOURNAL_SAFE
# below. `nodev`/`nosuid` stop a crafted image from carrying a device node or a
# setuid binary into the box's namespace; `noexec` stops anything on the volume
# being run at all.
BASE_OPTIONS: tuple[str, ...] = ("ro", "nodev", "nosuid", "noexec")

# The options that make "read-only" actually mean it.
#
# A dirty ext4/xfs/btrfs volume mounted with plain `-o ro` still REPLAYS ITS
# JOURNAL, which writes to the volume. On a box whose job is indexing other
# people's media that is both an integrity problem -- the evidence is modified by
# being read -- and a practical one, because the same write fails outright on a
# device the block layer has been told is read-only, and the mount then fails
# with an error that looks like a broken filesystem.
JOURNAL_SAFE: dict[str, tuple[str, ...]] = {
    "ext2": (),
    "ext3": ("noload",),
    "ext4": ("noload",),
    "xfs": ("norecovery",),
    "btrfs": ("nologreplay",),
    "f2fs": ("norecovery",),
}


class VolumePolicy(StrEnum):
    KNOWN = "known"
    GENERIC = "generic"
    REFUSED = "refused"


@dataclass(frozen=True)
class MountPlan:
    """How a single volume should be mounted, or why it will not be."""

    policy: VolumePolicy
    fstype: str | None
    options: tuple[str, ...]
    helper: str | None
    reason: str

    @property
    def mountable(self) -> bool:
        return self.policy is not VolumePolicy.REFUSED

    @property
    def option_string(self) -> str:
        return ",".join(self.options)


# Needs a key, a passphrase or an assembly step. Mounting a member device of one
# of these is either impossible or actively destructive, and guessing is not a
# decision to make on someone else's media.
REFUSED: dict[str, str] = {
    "crypto_LUKS": "LUKS container; no key",
    "BitLocker": "BitLocker volume; no recovery key",
    "zfs_member": "ZFS pool member; importing a foreign pool is not safe",
    "LVM2_member": "LVM physical volume; activating a foreign VG is not safe",
    "swap": "swap area; no files to index",
    "linux_raid_member": "MD RAID member; assembling a foreign array is not safe",
}

# Driver overrides. Absent from this table means "the in-kernel driver of the
# same name".
#
# NTFS goes through ntfs-3g rather than the in-kernel ntfs3 deliberately: this
# box parses filesystems it was handed by strangers, and FUSE keeps that parsing
# in a process that can crash without taking the kernel with it. It is slower,
# and that is the trade being made.
HELPERS: dict[str, str] = {
    "ntfs": "ntfs-3g",
    "ntfs3": "ntfs-3g",
    "apfs": "apfs-fuse",
}

# Filesystems with no concept of ownership, which therefore need to be told who
# owns the files they present.
NEEDS_OWNER: frozenset[str] = frozenset(
    {"vfat", "exfat", "ntfs", "ntfs3", "hfs", "hfsplus", "iso9660", "udf"}
)

# Filesystems that store names in a legacy code page unless told otherwise.
NEEDS_CHARSET: frozenset[str] = frozenset({"vfat", "exfat"})

KNOWN: frozenset[str] = frozenset(
    {
        "vfat",
        "exfat",
        "ntfs",
        "ntfs3",
        "ext2",
        "ext3",
        "ext4",
        "xfs",
        "btrfs",
        "f2fs",
        "hfs",
        "hfsplus",
        "iso9660",
        "udf",
        "apfs",
    }
)


def plan_mount(
    fstype: str | None,
    uid: int,
    gid: int,
    kernel_filesystems: frozenset[str] = frozenset(),
) -> MountPlan:
    """Decide how -- or whether -- to mount a volume of this type.

    `kernel_filesystems` is what /proc/filesystems reports. It only gates tier 3; a
    known type is attempted regardless, because its module may simply not be loaded yet
    and mount(8) will autoload it.
    """
    if not fstype:
        return MountPlan(
            VolumePolicy.REFUSED, None, (), None, "no recognisable filesystem"
        )

    if fstype in REFUSED:
        return MountPlan(VolumePolicy.REFUSED, fstype, (), None, REFUSED[fstype])

    if fstype not in KNOWN:
        if fstype not in kernel_filesystems:
            return MountPlan(
                VolumePolicy.REFUSED,
                fstype,
                (),
                None,
                f"the kernel has no driver for '{fstype}'",
            )
        # Baseline options only. Anything type-specific would be a guess, and a
        # wrong mount option fails the mount outright rather than being ignored.
        return MountPlan(
            VolumePolicy.GENERIC,
            None,
            BASE_OPTIONS,
            None,
            f"'{fstype}' is not in the table; attempting a generic read-only mount",
        )

    options = list(BASE_OPTIONS)
    options.extend(JOURNAL_SAFE.get(fstype, ()))

    if fstype in NEEDS_OWNER:
        options.extend([f"uid={uid}", f"gid={gid}", "umask=0077"])
    if fstype in NEEDS_CHARSET:
        options.append("iocharset=utf8")

    return MountPlan(
        VolumePolicy.KNOWN, fstype, tuple(options), HELPERS.get(fstype), ""
    )
