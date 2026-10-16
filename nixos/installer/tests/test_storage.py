"""What the installer is allowed to tear down before it repartitions a box.

`release_storage` closes every device-mapper node it can find, which is right: the disks
have to be let go of, and a box that has been installed twice -- or interrupted halfway
-- can be holding them through a mapping this code never made. The rule is exercised
here rather than in a VM because the cost of it being wrong is paid after the partition
table has already been rewritten.

The one exception is the `--lock-key` key store, and it is the exception a reader would
delete as redundant: the mapping is over the USB stick and holds nothing on the internal
disks, so closing it looks harmless. It is not. `install.run` opens it before the first
destructive step and hands it to `encrypt` afterwards, so a sweep that closes it takes
the key away between the two -- and the install dies with "Failed to open key file" on a
box whose disks have just been wiped.
"""

import pytest
from fakes import INSTALLER_ENVIRONMENT, FakeRunner

from loom_installer import constants, storage
from loom_installer.commands import CommandResult
from loom_installer.storage import mappings_to_close

KEY_STORE = "loom-keystore"


def test_everything_holding_the_disks_is_closed() -> None:
    # Including names this installer never created. A previous install, a manual
    # `cryptsetup open`, a different distribution's layout -- all of them keep the
    # partition table busy, and sgdisk fails on a busy device.
    present = ["control", "cryptroot", "loom-root", "somebody-elses-mapping"]

    assert mappings_to_close(present, KEY_STORE) == [
        "cryptroot",
        "loom-root",
        "somebody-elses-mapping",
    ]


def test_the_key_store_survives_the_sweep() -> None:
    # The regression. Found on hardware: the passphrase was accepted, the disks
    # were repartitioned, and then `encrypt` could not open the key it had been
    # given -- because this sweep had closed it three steps earlier.
    present = ["control", "cryptroot", KEY_STORE]

    assert mappings_to_close(present, KEY_STORE) == ["cryptroot"]


def test_an_unlocked_build_closes_everything_it_finds() -> None:
    # `mapping` is set on every stick, locked or not, so sparing it unconditionally
    # would leave a hole in the sweep on every ordinary one: a leftover mapping that
    # happened to carry the name would keep a disk busy with nothing to say why.
    # None is what `release_storage` passes when the build is not locked.
    present = ["control", "cryptroot", KEY_STORE]

    assert mappings_to_close(present, None) == ["cryptroot", KEY_STORE]


# The three branches of `pool_claimed_by_key`, which decides whether an unattended
# run installs over a box that is already indexing. The VM test
# (nixos/tests/scripts/loom_tests/install.py) drives the real function against a real
# LUKS container and is the stronger check -- but it is a ten-minute KVM build gated
# on what the MR touched, so the guard is worth a second that fails in a second.
ROOT_DEVICE = INSTALLER_ENVIRONMENT["LOOM_ROOT_DEVICE"]
VOLUME_GROUP = INSTALLER_ENVIRONMENT["LOOM_VG_NAME"]
KEY_DEVICE = "/dev/disk/by-partlabel/loom-key"

ACTIVATE = ["vgchange", "--activate", "y", VOLUME_GROUP]
DEACTIVATE = ["vgchange", "--activate", "n", VOLUME_GROUP]
VG_ATTR = ["vgs", "--noheadings", "--options", "vg_attr", VOLUME_GROUP]
LUKS_DUMP = ["cryptsetup", "luksDump", ROOT_DEVICE]
TEST_PASSPHRASE = [
    "cryptsetup",
    "luksOpen",
    "--test-passphrase",
    "--key-file",
    KEY_DEVICE,
    "--keyfile-size",
    str(constants.KEY_BYTES),
    ROOT_DEVICE,
]


def _claimable_box(runner: FakeRunner) -> FakeRunner:
    """A box this very stick finished installing."""
    runner.block_devices.add(ROOT_DEVICE)
    runner.succeeds(ACTIVATE)
    runner.succeeds(DEACTIVATE)
    runner.succeeds(VG_ATTR, "  wz--n-\n")
    runner.succeeds(LUKS_DUMP, f"Version:\t2\nLabel:\t{constants.INSTALLED_LABEL}\n")
    runner.succeeds(TEST_PASSPHRASE)
    return runner


def test_a_box_this_stick_installed_is_claimed() -> None:
    runner = _claimable_box(FakeRunner())

    assert storage.pool_claimed_by_key(runner, KEY_DEVICE) is True


def test_a_box_with_no_root_device_is_not_claimed() -> None:
    # Nothing to open, so nothing to ask cryptsetup about -- and asking anyway would
    # be a `cryptsetup` call against a path that is not there.
    runner = _claimable_box(FakeRunner())
    runner.block_devices.discard(ROOT_DEVICE)

    assert storage.pool_claimed_by_key(runner, KEY_DEVICE) is False
    assert not any(call[:1] == ["cryptsetup"] for call in runner.calls)


def test_a_container_another_stick_made_is_not_claimed() -> None:
    # The half of the guard that keeps re-provisioning unattended: a re-flashed
    # stick carries a fresh key and must still be allowed to install.
    runner = _claimable_box(FakeRunner())
    runner.commands[" ".join(TEST_PASSPHRASE)] = CommandResult(2, "", "No key")

    assert storage.pool_claimed_by_key(runner, KEY_DEVICE) is False


def test_a_half_written_pool_is_not_claimed() -> None:
    # `encrypt` has run and `stamp_pool_installed` has not, which is what a power
    # loss during the twenty-minute copy leaves behind. Claiming it would strand the
    # box at a menu insisting it had already installed itself.
    runner = _claimable_box(FakeRunner())
    runner.succeeds(LUKS_DUMP, "Version:\t2\nLabel:\t(no label)\n")

    assert storage.pool_claimed_by_key(runner, KEY_DEVICE) is False


def test_looking_leaves_the_group_as_it_was_found() -> None:
    # Both outcomes deactivate, which is the "leave the box as it was found" promise
    # an early return would quietly lose.
    for passphrase in (CommandResult(0, "", ""), CommandResult(2, "", "No key")):
        runner = _claimable_box(FakeRunner())
        runner.commands[" ".join(TEST_PASSPHRASE)] = passphrase

        storage.pool_claimed_by_key(runner, KEY_DEVICE)

        assert DEACTIVATE in runner.calls


def test_a_group_the_operator_activated_is_left_active() -> None:
    # The live case: an ALREADY_INSTALLED box whose operator activated the group from
    # the rescue shell to copy data off it. The probe is read-only by contract.
    runner = _claimable_box(FakeRunner())
    runner.succeeds(VG_ATTR, "  wz--na\n")

    storage.pool_claimed_by_key(runner, KEY_DEVICE)

    assert DEACTIVATE not in runner.calls


def test_a_pool_reaching_outside_the_confirmed_disks_stops_the_run() -> None:
    """`vgremove` addresses LVM by name, and this stick sets no device filter.

    So a `loom` volume group on a disk `target_disks` excluded -- a SATA disk, a pulled
    NVMe in a USB caddy -- is destroyed by a run that never showed it to the operator.
    """
    runner = FakeRunner()
    runner.succeeds(
        [
            "vgs",
            "--noheadings",
            "--options",
            "pv_name",
            "--select",
            f"vg_name={VOLUME_GROUP}",
        ],
        "  /dev/sdb1\n",
    )
    runner.succeeds(
        [
            "lsblk",
            "--noheadings",
            "--raw",
            "--paths",
            "--output",
            "PKNAME",
            "/dev/sdb1",
        ],
        "/dev/sdb\n",
    )

    assert storage.pool_disks_outside(runner, ["/dev/nvme0n1"]) == ["/dev/sdb"]

    with pytest.raises(storage.StorageError, match="/dev/sdb"):
        storage.discard_pool(runner, targets=["/dev/nvme0n1"])

    assert not any("vgremove" in call for call in runner.calls)


def test_a_pool_confined_to_the_confirmed_disks_is_destroyed() -> None:
    runner = FakeRunner()
    runner.succeeds(
        [
            "vgs",
            "--noheadings",
            "--options",
            "pv_name",
            "--select",
            f"vg_name={VOLUME_GROUP}",
        ],
        "  /dev/nvme0n1p2\n",
    )
    runner.succeeds(
        [
            "lsblk",
            "--noheadings",
            "--raw",
            "--paths",
            "--output",
            "PKNAME",
            "/dev/nvme0n1p2",
        ],
        "/dev/nvme0n1\n",
    )

    storage.discard_pool(runner, targets=["/dev/nvme0n1"])

    assert ["vgremove", "--force", VOLUME_GROUP] in runner.calls
