"""Letting go of the pool, and destroying it.

Both destructive paths need the first of these before they can touch a partition table,
and the already-installed probe needs the inverse of it afterwards. Shared rather than
written twice because the order is the part that matters: the LUKS mapping sits on the
logical volume, so closing dm-crypt has to come first or the group is still in use and
`vgchange --activate n` quietly does nothing.
"""

import glob
import os

from loom_installer import constants
from loom_installer.commands import CommandRunner
from loom_installer.settings import settings


def release_storage(runner: CommandRunner) -> None:
    """Let go of whatever is holding the internal disks, without destroying it."""
    runner.run(["swapoff", "--all"])
    runner.run(["umount", "--recursive", constants.MOUNT])

    for mapping in sorted(glob.glob("/dev/mapper/*")):
        name = os.path.basename(mapping)
        if name == "control" or not runner.is_block_device(mapping):
            continue
        runner.run(["cryptsetup", "close", name])

    deactivate(runner)


def discard_pool(runner: CommandRunner) -> None:
    """Destroy the pool itself, so the disks under it can be repartitioned.

    Deliberately separate from `release_storage`: the probe deactivates, the installer
    destroys, and conflating the two would make looking at a box indistinguishable from
    reinstalling it.
    """
    release_storage(runner)
    runner.run(["vgremove", "--force", settings().storage.volume_group])
    # Drop what lvm cached about devices that are about to stop existing. Without
    # it `vgcreate` can still see the group it was just told to forget.
    runner.run(["pvscan", "--cache"])


def activate(runner: CommandRunner) -> None:
    runner.run(["vgchange", "--activate", "y", settings().storage.volume_group])


def deactivate(runner: CommandRunner) -> None:
    """An active group keeps the partition tables busy, which matters because the menu
    is still running and its next option may be a wipe."""
    runner.run(["vgchange", "--activate", "n", settings().storage.volume_group])


def pool_claimed_by_key(runner: CommandRunner, key_device: str) -> bool:
    """Whether the internal disks already hold a pool *this* stick's key unlocks.

    True means this very stick installed this very box, and it is what replaces the
    typed INSTALL word for an unattended install. The accident it guards against is
    the one the design otherwise invites: the stick stays plugged in forever, so a
    cleared NVRAM or a firmware that re-scans removable media boots the installer
    again, and without this the box would quietly reinstall over its own indexed
    data with nobody at the keyboard.

    A re-flashed stick carries a fresh key, so this never blocks re-provisioning. It
    only blocks a stick meeting the box it already installed.
    """
    root_device = settings().storage.root_device

    activate(runner)
    claimed = (
        runner.is_block_device(root_device)
        and runner.run(
            [
                "cryptsetup",
                "luksOpen",
                "--test-passphrase",
                "--key-file",
                key_device,
                "--keyfile-size",
                str(constants.KEY_BYTES),
                root_device,
            ]
        ).ok
    )
    # Leave the box as it was found. An active group would also make the partition
    # table busy if the operator picks Install off the menu anyway.
    deactivate(runner)

    return claimed
