"""Mounting a volume read-only, and meaning it."""

import logging
import os
import subprocess
from dataclasses import dataclass

from loom_usb_ingest.devices import Volume
from loom_usb_ingest.filesystems import MountPlan, VolumePolicy, plan_mount

logger = logging.getLogger(__name__)

MOUNT_TIMEOUT_S = 120


@dataclass(frozen=True)
class MountedVolume:
    volume: Volume
    mountpoint: str
    plan: MountPlan


@dataclass(frozen=True)
class SkippedVolume:
    volume: Volume
    reason: str


def kernel_filesystems() -> frozenset[str]:
    """What /proc/filesystems reports, for the generic tier's support check."""
    try:
        with open("/proc/filesystems", "r", encoding="utf-8") as handle:
            return frozenset(
                line.split()[-1] for line in handle if line.strip()
            )
    except OSError:
        return frozenset()


def set_block_read_only(device: str) -> bool:
    """Tell the block layer the device is read-only, before anything mounts it.

    Belt to the `ro` mount option's braces, and stronger than it: this is
    enforced below the filesystem driver, so a driver that decides to write
    anyway -- a journal replay, a dirty-bit clear -- is refused by the kernel
    rather than trusted not to try.
    """
    try:
        subprocess.run(
            ["blockdev", "--setro", device],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (subprocess.SubprocessError, OSError) as error:
        # Not fatal. Some USB bridges reject the ioctl, and the mount options
        # still stand; say so rather than refusing to read the stick at all.
        logger.warning("Could not set %s read-only at the block layer: %s", device, error)
        return False


def _mount_argv(device: str, mountpoint: str, plan: MountPlan) -> list[str]:
    if plan.helper:
        # FUSE helpers are executed directly rather than through `mount -t`.
        # mount(8) would have to find a `mount.<type>` helper on a search path a
        # systemd unit does not necessarily have, and apfs-fuse ships no such
        # helper at all. Calling the binary is unambiguous.
        return [plan.helper, "-o", plan.option_string, device, mountpoint]

    argv = ["mount", "-o", plan.option_string]
    if plan.fstype:
        argv += ["-t", plan.fstype]
    return argv + [device, mountpoint]


def mount_volume(
    volume: Volume, mountpoint: str, uid: int, gid: int, supported: frozenset[str]
) -> MountedVolume | SkippedVolume:
    """Mount one volume read-only, or explain why it was not mounted."""
    plan = plan_mount(volume.fstype, uid, gid, supported)

    if plan.policy is VolumePolicy.REFUSED:
        logger.info("Skipping %s: %s", volume.path, plan.reason)
        return SkippedVolume(volume, plan.reason)

    if plan.policy is VolumePolicy.GENERIC:
        logger.info("%s: %s", volume.path, plan.reason)

    set_block_read_only(volume.path)
    os.makedirs(mountpoint, mode=0o700, exist_ok=True)

    try:
        subprocess.run(
            _mount_argv(volume.path, mountpoint, plan),
            check=True,
            capture_output=True,
            text=True,
            timeout=MOUNT_TIMEOUT_S,
        )
    except subprocess.CalledProcessError as error:
        reason = (error.stderr or "").strip() or f"mount exited {error.returncode}"
        logger.warning("Could not mount %s: %s", volume.path, reason)
        _remove_mountpoint(mountpoint)
        return SkippedVolume(volume, reason)
    except (subprocess.SubprocessError, OSError) as error:
        logger.warning("Could not mount %s: %s", volume.path, error)
        _remove_mountpoint(mountpoint)
        return SkippedVolume(volume, str(error))

    logger.info(
        "Mounted %s at %s (%s, %s)",
        volume.path,
        mountpoint,
        plan.fstype or "auto",
        plan.option_string,
    )
    return MountedVolume(volume, mountpoint, plan)


def unmount(mountpoint: str) -> None:
    """Unmount, lazily if it comes to that.

    A lazy unmount is the right answer here rather than a failure: the usual
    cause is the operator having already pulled the stick, and leaving a stale
    mount behind would block the same device being ingested again later.
    """
    for argv in (["umount", mountpoint], ["umount", "--lazy", mountpoint]):
        try:
            subprocess.run(argv, check=True, capture_output=True, timeout=60)
            break
        except (subprocess.SubprocessError, OSError):
            continue
    _remove_mountpoint(mountpoint)


def _remove_mountpoint(mountpoint: str) -> None:
    try:
        os.rmdir(mountpoint)
    except OSError:
        pass
