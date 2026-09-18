import pytest
from loom_usb_ingest.filesystems import (
    BASE_OPTIONS,
    VolumePolicy,
    plan_mount,
)

UID = 1000
GID = 100
KERNEL = frozenset({"ext4", "vfat", "minix", "jfs", "ufs"})


def _plan(fstype):
    return plan_mount(fstype, UID, GID, KERNEL)


@pytest.mark.parametrize("fstype", ["vfat", "exfat", "ntfs", "ext4", "xfs", "hfsplus"])
def test_every_known_filesystem_is_mounted_read_only(fstype):
    plan = _plan(fstype)

    assert plan.policy is VolumePolicy.KNOWN
    for option in BASE_OPTIONS:
        assert option in plan.options


@pytest.mark.parametrize(
    "fstype,expected",
    [
        ("ext3", "noload"),
        ("ext4", "noload"),
        ("xfs", "norecovery"),
        ("btrfs", "nologreplay"),
        ("f2fs", "norecovery"),
    ],
)
def test_journalled_filesystems_never_replay_their_journal(fstype, expected):
    """`-o ro` alone still writes to a dirty volume. This is the actual guarantee.

    It is both an integrity property -- the media must not be modified by being
    read -- and a practical one, since the same write fails outright once the
    block device has been set read-only.
    """
    assert expected in _plan(fstype).options


def test_ntfs_goes_through_fuse_not_the_kernel_driver():
    """Deliberate: strangers' filesystems get parsed outside the kernel."""
    assert _plan("ntfs").helper == "ntfs-3g"
    assert _plan("ntfs3").helper == "ntfs-3g"


def test_ownerless_filesystems_are_given_an_owner():
    plan = _plan("vfat")

    assert f"uid={UID}" in plan.options
    assert f"gid={GID}" in plan.options
    assert "umask=0077" in plan.options


def test_fat_family_is_told_to_read_names_as_utf8():
    assert "iocharset=utf8" in _plan("exfat").options


@pytest.mark.parametrize(
    "fstype", ["crypto_LUKS", "BitLocker", "zfs_member", "LVM2_member", "swap"]
)
def test_container_formats_are_refused_with_a_reason(fstype):
    plan = _plan(fstype)

    assert plan.policy is VolumePolicy.REFUSED
    assert not plan.mountable
    assert plan.reason


def test_an_unrecognised_but_supported_filesystem_gets_a_generic_attempt():
    """Tier 3: coverage is not capped by what the table happens to list."""
    plan = _plan("minix")

    assert plan.policy is VolumePolicy.GENERIC
    assert plan.fstype is None  # mount decides
    assert plan.options == BASE_OPTIONS


def test_a_filesystem_the_kernel_cannot_mount_is_refused():
    plan = _plan("befs")

    assert plan.policy is VolumePolicy.REFUSED
    assert "no driver" in plan.reason


def test_a_volume_with_no_filesystem_is_refused():
    assert plan_mount(None, UID, GID, KERNEL).policy is VolumePolicy.REFUSED
