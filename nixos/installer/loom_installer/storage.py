"""Letting go of the pool, and destroying it.

Both destructive paths need the first of these before they can touch a partition table,
and the already-installed probe needs the inverse of it afterwards. Shared rather than
written twice because the order is the part that matters: the LUKS mapping sits on the
logical volume, so closing dm-crypt has to come first or the group is still in use and
`vgchange --activate n` quietly does nothing.
"""

import glob
import os

from loom_installer import constants, devices
from loom_installer.commands import CommandRunner
from loom_installer.settings import settings


class StorageError(RuntimeError):
    """Something about the box makes a destructive step unsafe to take."""


def mappings_to_close(present: list[str], key_store: str | None) -> list[str]:
    """Which device-mapper names `release_storage` must close.

    Pure, and separate from the sweep that finds them, for the same reason
    decision.py is: this is a rule about what may be destroyed, and a rule like
    that should be exercisable without a box. tests/test_storage.py is the table.

    Everything goes, because what has to go is whatever is holding the disks --
    and a box that has been installed twice, or interrupted, can be holding them
    through something this code never created. Two exceptions:

      * `control`, which is device-mapper's own control node and not a mapping.
      * The `--lock-key` key store. That one is a mapping over the *USB stick*,
        so it holds nothing here -- and it is the device the caller is about to
        encrypt with. `install.run` opens it before any of this and hands it to
        `encrypt` afterwards; closing it in between takes the key away and fails
        the install with "Failed to open key file", after the disks have already
        been repartitioned.

    `key_store` is None on a stick without `--lock-key`, where there is no such
    mapping to spare. Passing the name unconditionally would leave a hole in the
    sweep on every ordinary stick: a leftover mapping that happened to carry that
    name would keep a disk busy, and nothing here would say why.
    """
    spared = {"control"} | ({key_store} if key_store is not None else set())
    return [name for name in present if name not in spared]


def release_storage(runner: CommandRunner) -> None:
    """Let go of whatever is holding the internal disks, without destroying it."""
    runner.run(["swapoff", "--all"])
    runner.run(["umount", "--recursive", constants.MOUNT])

    key_store = settings().key_store
    present = [
        os.path.basename(mapping)
        for mapping in sorted(glob.glob("/dev/mapper/*"))
        if runner.is_block_device(mapping)
    ]
    for name in mappings_to_close(
        present, key_store.mapping if key_store.locked else None
    ):
        runner.run(["cryptsetup", "close", name])

    deactivate(runner)


def pool_members(runner: CommandRunner) -> list[str]:
    """The physical volumes the pool is built on, as device paths."""
    listing = runner.output(
        [
            "vgs",
            "--noheadings",
            "--options",
            "pv_name",
            "--select",
            f"vg_name={settings().storage.volume_group}",
        ]
    )
    return [line.strip() for line in listing.splitlines() if line.strip()]


def pool_disks_outside(runner: CommandRunner, targets: list[str]) -> list[str]:
    """Disks carrying a volume group of this name that are not in `targets`.

    `vgremove` and `vgchange` address LVM **by group name**, and this stick configures
    no LVM device filter -- so every one of these is destroyed by a `vgremove loom`
    despite never appearing in the "THE FOLLOWING WILL BE DESTROYED" list that
    `target_disks` built:

      * a SATA or SAS disk carrying a `loom` VG, excluded by the NVMe regex;
      * a second NVMe excluded as removable, USB or mounted;
      * a pulled Loom NVMe in a USB caddy -- attached by the operator precisely to
        copy data off it.

    `wipe.erase_pool_keys` makes it worse: it activates the group globally and then
    `luksErase`s a name-resolved device-mapper path, which is unrecoverable.
    """
    allowed = set(targets)
    outside = []
    for member in pool_members(runner):
        parent = devices.parent_of(runner, member)
        # No parent means the PV is a whole disk rather than a partition.
        disk = parent or member
        if disk not in allowed:
            outside.append(disk)
    return sorted(set(outside))


def discard_pool(runner: CommandRunner, targets: list[str] | None = None) -> None:
    """Destroy the pool itself, so the disks under it can be repartitioned.

    Deliberately separate from `release_storage`: the probe deactivates, the installer
    destroys, and conflating the two would make looking at a box indistinguishable from
    reinstalling it.

    `targets` is the set of disks the operator was shown and confirmed. When it is
    given, a volume group of this name that reaches outside it stops the run rather than
    being destroyed -- see `pool_disks_outside`. It defaults to None only for the
    callers that have already established there is nothing else attached.
    """
    if targets is not None:
        outside = pool_disks_outside(runner, targets)
        if outside:
            raise StorageError(
                "A volume group named "
                f"{settings().storage.volume_group} also lives on "
                f"{', '.join(outside)}, which is not one of the disks this run may "
                "write to. Destroying it by name would take that disk's data with it. "
                "Detach it and try again."
            )

    release_storage(runner)
    runner.run(["vgremove", "--force", settings().storage.volume_group])
    # Drop what lvm cached about devices that are about to stop existing. Without
    # it `vgcreate` can still see the group it was just told to forget.
    runner.run(["pvscan", "--cache"])


def activate(runner: CommandRunner) -> None:
    runner.run(["vgchange", "--activate", "y", settings().storage.volume_group])


def is_active(runner: CommandRunner) -> bool:
    """Whether the volume group is active right now.

    `vg_attr`'s sixth character is the activation state: `a` for active. Read so that a
    read-only probe can put the box back exactly as it found it rather than deactivating
    unconditionally.
    """
    attributes = runner.output(
        [
            "vgs",
            "--noheadings",
            "--options",
            "vg_attr",
            settings().storage.volume_group,
        ]
    ).strip()
    return len(attributes) >= 6 and attributes[5] == "a"


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

    Two conditions, not one. The passphrase test alone is satisfied from the instant
    `install.encrypt` returns -- twenty minutes before there is a system on the disk
    -- so on its own a power loss during `install_system` leaves a box that answers
    "already installed" with no bootloader and no NVRAM entry, sitting at the menu
    refusing to try again. The LUKS2 label is written last, by
    `install.stamp_pool_installed`, so it means *finished*.
    """
    root_device = settings().storage.root_device

    # Whether the group was already active decides whether this probe may deactivate
    # it afterwards. It is read-only by contract, and an operator who activated the
    # group from the rescue shell to copy data off an ALREADY_INSTALLED box -- the one
    # box where this runs -- would otherwise have it torn down under them on the next
    # menu redraw.
    was_active = is_active(runner)

    activate(runner)
    claimed = (
        runner.is_block_device(root_device)
        and _is_labelled_installed(runner, root_device)
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
    # Leave the box as it was found. An active group would make the partition table
    # busy if the operator picks Install off the menu, so the common case still
    # deactivates.
    if not was_active:
        deactivate(runner)

    return claimed


def _is_labelled_installed(runner: CommandRunner, root_device: str) -> bool:
    """Whether the container carries the label a finished install stamps on it."""
    dump = runner.output(["cryptsetup", "luksDump", root_device])
    return any(
        line.split(":", 1)[1].strip() == constants.INSTALLED_LABEL
        for line in dump.splitlines()
        if line.strip().lower().startswith("label:")
    )
