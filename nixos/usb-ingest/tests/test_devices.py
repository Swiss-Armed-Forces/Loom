"""The exclusion rules. The key stick must never be ingested."""

import pytest
from loom_usb_ingest.devices import (
    Disk,
    GuardState,
    KeyGuard,
    Volume,
    classify_disk,
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


def _disk(kname, volumes=(), size=8_000_000_000):
    return Disk(
        path=f"/dev/{kname}", kernel_name=kname, size=size, volumes=tuple(volumes)
    )


def test_an_ordinary_stick_is_ingested():
    verdict = classify_disk(_disk("sdc", [_volume("/dev/sdc1")]), ARMED, NO_PROTECTED)

    assert verdict.ingest


def test_the_armed_key_disk_is_never_ingested():
    """The central guarantee. Pulling this stick powers the box off."""
    verdict = classify_disk(_disk("sdb", [_volume("/dev/sdb1")]), ARMED, NO_PROTECTED)

    assert not verdict.ingest
    assert "key guard" in verdict.reason


@pytest.mark.parametrize(
    "partlabel",
    ["loom-key", "loom-esp", "loom-root-luks", "loom-live-esp", "loom-live-store"],
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
