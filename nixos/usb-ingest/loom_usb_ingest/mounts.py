"""Mounting a volume read-only, and meaning it.

Everything this module shells out to goes through an injected runner, the same way
`transfer.WaitHooks` and `loom_installer.commands.CommandRunner` do. This is the one
module that touches strangers' filesystems, so its failure paths -- a corrupt signature,
a stick pulled mid-copy -- are the ones worth exercising, and they can only be exercised
without patching if the commands come in from outside.
"""

import logging
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from loom_usb_ingest.devices import Volume
from loom_usb_ingest.filesystems import MountPlan, VolumePolicy, plan_mount

logger = logging.getLogger(__name__)

MOUNT_TIMEOUT_S = 120
BLOCKDEV_TIMEOUT_S = 30
UMOUNT_TIMEOUT_S = 60


@dataclass(frozen=True)
class CommandOutcome:
    """How one command went.

    A command that could not be run at all is a failure too.     `stderr` carries the
    reason either way -- what the tool printed, or what Python     said about not being
    able to start it -- because both end up in front of the     operator as the reason a
    volume was skipped.
    """

    returncode: int
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


# `mount`, `blockdev` and `umount`, as this module reaches them.
Runner = Callable[[list[str], int], CommandOutcome]


def run_command(argv: list[str], timeout: int) -> CommandOutcome:
    """The real runner."""
    try:
        completed = subprocess.run(
            argv, check=False, capture_output=True, text=True, timeout=timeout
        )
    except (subprocess.SubprocessError, OSError) as error:
        # 127 is the shell's "could not execute", which is what this is.
        return CommandOutcome(127, str(error))
    return CommandOutcome(completed.returncode, completed.stderr or "")


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
            return frozenset(line.split()[-1] for line in handle if line.strip())
    except OSError:
        return frozenset()


def set_block_read_only(device: str, run: Runner = run_command) -> bool:
    """Tell the block layer the device is read-only, before anything mounts it.

    Belt to the `ro` mount option's braces, and stronger than it: this is
    enforced below the filesystem driver, so a driver that decides to write
    anyway -- a journal replay, a dirty-bit clear -- is refused by the kernel
    rather than trusted not to try.
    """
    outcome = run(["blockdev", "--setro", device], BLOCKDEV_TIMEOUT_S)
    if outcome.ok:
        return True

    # Not fatal. Some USB bridges reject the ioctl, and the mount options
    # still stand; say so rather than refusing to read the stick at all.
    logger.warning(
        "Could not set %s read-only at the block layer: %s",
        device,
        outcome.stderr.strip() or f"blockdev exited {outcome.returncode}",
    )
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
    volume: Volume,
    mountpoint: str,
    uid: int,
    gid: int,
    supported: frozenset[str],
    run: Runner = run_command,
) -> MountedVolume | SkippedVolume:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Mount one volume read-only, or explain why it was not mounted."""
    plan = plan_mount(volume.fstype, uid, gid, supported)

    if plan.policy is VolumePolicy.REFUSED:
        logger.info("Skipping %s: %s", volume.path, plan.reason)
        return SkippedVolume(volume, plan.reason)

    if plan.policy is VolumePolicy.GENERIC:
        logger.info("%s: %s", volume.path, plan.reason)

    set_block_read_only(volume.path, run)
    os.makedirs(mountpoint, mode=0o700, exist_ok=True)

    outcome = run(_mount_argv(volume.path, mountpoint, plan), MOUNT_TIMEOUT_S)
    if not outcome.ok:
        reason = outcome.stderr.strip() or f"mount exited {outcome.returncode}"
        logger.warning("Could not mount %s: %s", volume.path, reason)
        # Left behind, an empty mountpoint under the device's directory is
        # indistinguishable from a mounted volume to anything that walks the tree.
        _remove_mountpoint(mountpoint)
        return SkippedVolume(volume, reason)

    logger.info(
        "Mounted %s at %s (%s, %s)",
        volume.path,
        mountpoint,
        plan.fstype or "auto",
        plan.option_string,
    )
    return MountedVolume(volume, mountpoint, plan)


def unmount(mountpoint: str, run: Runner = run_command) -> None:
    """Unmount, lazily if it comes to that.

    A lazy unmount is the right answer here rather than a failure: the usual
    cause is the operator having already pulled the stick, and leaving a stale
    mount behind would block the same device being ingested again later.
    """
    for argv in (["umount", mountpoint], ["umount", "--lazy", mountpoint]):
        if run(argv, UMOUNT_TIMEOUT_S).ok:
            break
    _remove_mountpoint(mountpoint)


def _remove_mountpoint(mountpoint: str) -> None:
    try:
        os.rmdir(mountpoint)
    except OSError:
        pass
