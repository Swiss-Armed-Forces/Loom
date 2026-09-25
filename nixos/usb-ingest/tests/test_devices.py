"""The exclusion rules.

The key stick must never be ingested.
"""

import pytest

from loom_usb_ingest.devices import (
    Disk,
    GuardState,
    KeyGuard,
    Volume,
    classify_disk,
    disk_from_lsblk,
    disks_from_lsblk_inverse,
)

ARMED = KeyGuard(GuardState.ARMED, "sdb")
IDLE = KeyGuard(GuardState.IDLE, None)
NO_PROTECTED: frozenset[str] = frozenset()


def _volume(path, partlabel=None, fstype="vfat", mountpoint=None):
    return Volume(
        path=path,
        fstype=fstype,
        label=None,
        partlabel=partlabel,
        size=1024,
        mountpoint=mountpoint,
    )


def _rows(rows):
    """`lsblk --inverse --noheadings --output TYPE,KNAME` output, as text."""
    return "".join(f"{row}\n" for row in rows)


def _disk(kname, volumes=(), size=8_000_000_000):
    return Disk(
        path=f"/dev/{kname}", kernel_name=kname, size=size, volumes=tuple(volumes)
    )


def test_an_ordinary_stick_is_ingested():
    verdict = classify_disk(_disk("sdc", [_volume("/dev/sdc1")]), ARMED, NO_PROTECTED)

    assert verdict.ingest


def test_the_armed_key_disk_is_never_ingested():
    """The central guarantee.

    Pulling this stick powers the box off.
    """
    verdict = classify_disk(_disk("sdb", [_volume("/dev/sdb1")]), ARMED, NO_PROTECTED)

    assert not verdict.ingest
    assert "key guard" in verdict.reason


@pytest.mark.parametrize(
    "partlabel",
    [
        "loom-key",
        "loom-esp",
        "loom-live-esp",
        "loom-live-store",
        # `install.partition` writes `loom-pv<N>` onto every pool member, so on a
        # two-NVMe box the second disk carries this and nothing else.
        "loom-pv0",
        "loom-pv1",
    ],
)
def test_loom_media_is_excluded_even_when_the_guard_is_idle(partlabel):
    """A box booted on the recovery passphrase never arms the guard.

    Partition labels are the weaker fallback, and they are what stops another
    box's key stick -- or the installer stick, carrying ~60 GB of container
    images -- being ingested in that state.
    """
    disk = _disk("sdd", [_volume("/dev/sdd1", partlabel=partlabel)])

    verdict = classify_disk(disk, IDLE, NO_PROTECTED)

    assert not verdict.ingest
    assert partlabel in verdict.reason


def test_a_foreign_stick_is_still_ingested_when_the_guard_is_idle():
    verdict = classify_disk(_disk("sdc", [_volume("/dev/sdc1")]), IDLE, NO_PROTECTED)

    assert verdict.ingest


def test_the_appliances_own_disks_are_excluded():
    verdict = classify_disk(
        _disk("nvme0n1", [_volume("/dev/nvme0n1p1")]), ARMED, frozenset({"nvme0n1"})
    )

    assert not verdict.ingest
    assert "root or boot" in verdict.reason


def test_a_fully_mounted_disk_is_left_alone():
    disk = _disk("sde", [_volume("/dev/sde1", mountpoint="/mnt/somewhere")])

    assert not classify_disk(disk, ARMED, NO_PROTECTED).ingest


def test_a_partly_mounted_disk_is_still_ingested():
    disk = _disk(
        "sde",
        [_volume("/dev/sde1", mountpoint="/mnt/x"), _volume("/dev/sde2")],
    )

    assert classify_disk(disk, ARMED, NO_PROTECTED).ingest


def test_a_disk_with_no_volumes_is_not_treated_as_fully_mounted():
    assert classify_disk(_disk("sdf"), ARMED, NO_PROTECTED).ingest


def test_guard_is_only_authoritative_when_armed_with_a_device():
    assert ARMED.authoritative
    assert not IDLE.authoritative
    assert not KeyGuard(GuardState.ARMED, None).authoritative
    assert not KeyGuard(GuardState.DISARMED, "sdb").authoritative


def test_a_device_mapper_root_resolves_to_the_disks_under_it():
    """The protected-disk rule is only alive if this hop works.

    The appliance installs LUKS on LVM, so `findmnt --target /` names a dm node and the
    disk wanted is three hops down. Answering `dm-0` here would make `classify_disk`'s
    first rule unable to match the box's own root, ever.
    """
    disks = disks_from_lsblk_inverse(
        _rows(["lvm dm-2", "crypt dm-0", "part nvme0n1p2", "disk nvme0n1"])
    )

    assert disks == frozenset({"nvme0n1"})


def test_a_whole_disk_resolves_to_itself():
    assert disks_from_lsblk_inverse(_rows(["disk sdb"])) == frozenset({"sdb"})


def test_a_root_spanning_two_disks_protects_both():
    disks = disks_from_lsblk_inverse(
        _rows(
            [
                "lvm dm-2",
                "part nvme0n1p2",
                "disk nvme0n1",
                "part nvme1n1p1",
                "disk nvme1n1",
            ]
        )
    )

    assert disks == frozenset({"nvme0n1", "nvme1n1"})


def test_a_disk_is_read_off_lsblk_with_its_volumes():
    disk = disk_from_lsblk(
        [
            {
                "path": "/dev/sdb",
                "kname": "sdb",
                "type": "disk",
                "size": 8_000_000_000,
                "children": [
                    {
                        "path": "/dev/sdb1",
                        "kname": "sdb1",
                        "fstype": "vfat",
                        "partlabel": "loom-key",
                        "size": 1024,
                    }
                ],
            }
        ],
        "/dev/sdb",
        {"ID_BUS": "usb"},
    )

    assert disk.kernel_name == "sdb"
    assert disk.path == "/dev/sdb"
    assert [volume.path for volume in disk.volumes] == ["/dev/sdb1"]
    assert disk.partlabels == frozenset({"loom-key"})
    assert disk.properties == {"ID_BUS": "usb"}


def test_a_superfloppy_is_one_volume_covering_the_whole_device():
    disk = disk_from_lsblk(
        [{"path": "/dev/sdb", "kname": "sdb", "fstype": "vfat", "size": 1024}],
        "/dev/sdb",
        {},
    )

    assert [volume.path for volume in disk.volumes] == ["/dev/sdb"]


def test_a_holder_nested_under_a_partition_is_not_a_volume_of_the_stick():
    # The shape `lsblk --tree` actually produces for a stick carrying a LUKS
    # container: the crypt node is a child of the partition holding it, never a
    # sibling. Only the partition is a volume; mounting the mapping would mean
    # mounting a stranger's unlocked container.
    disk = disk_from_lsblk(
        [
            {
                "path": "/dev/sdb",
                "kname": "sdb",
                "type": "disk",
                "size": 8_000_000_000,
                "children": [
                    {
                        "path": "/dev/sdb1",
                        "kname": "sdb1",
                        "type": "part",
                        "fstype": "crypto_LUKS",
                        "size": 1024,
                        "children": [
                            {
                                "path": "/dev/mapper/root",
                                "kname": "dm-0",
                                "type": "crypt",
                                "fstype": "ext4",
                            }
                        ],
                    }
                ],
            }
        ],
        "/dev/sdb",
        {},
    )

    assert disk.kernel_name == "sdb"
    assert [volume.path for volume in disk.volumes] == ["/dev/sdb1"]


def test_the_kernel_name_is_bare_even_when_lsblk_reports_a_path():
    # `lsblk --paths` puts a full path in KNAME, and a kernel_name of
    # "/dev/sdb" matches neither what `parent_disk` returns for the key stick
    # nor what `protected_disks` returns for the root -- so every exclusion in
    # `classify_disk` quietly stops matching and the key stick gets ingested.
    disk = disk_from_lsblk(
        [{"path": "/dev/sdb", "kname": "/dev/sdb", "size": 1024}], "/dev/sdb", {}
    )

    assert disk.kernel_name == "sdb"
    assert not classify_disk(disk, ARMED, NO_PROTECTED).ingest
    assert not classify_disk(disk, IDLE, frozenset({"sdb"})).ingest
