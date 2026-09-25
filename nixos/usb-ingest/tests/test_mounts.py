"""How a volume is actually mounted, and what happens when it will not mount.

This is the module that touches strangers' filesystems, so the branches that matter are
the ones nobody gets to see: the FUSE helper being invoked as a binary rather than
through `mount -t`, a corrupt signature coming back as a reason on the console, and the
fall through to a lazy unmount when the stick has already been pulled.

The commands are injected rather than patched -- see `mounts.Runner`.
"""

import os

from loom_usb_ingest.devices import Volume
from loom_usb_ingest.mounts import (
    CommandOutcome,
    MountedVolume,
    SkippedVolume,
    mount_volume,
    set_block_read_only,
    unmount,
)

UID = 1000
GID = 100
KERNEL = frozenset({"ext4", "vfat", "minix"})


class FakeRunner:
    """Records every command, and answers each by its first two words."""

    def __init__(self, answers=None):
        self.calls: list[list[str]] = []
        self._answers = answers or {}

    def __call__(self, argv: list[str], timeout: int) -> CommandOutcome:
        assert timeout > 0
        self.calls.append(list(argv))
        for key, outcome in self._answers.items():
            if argv[: len(key)] == list(key):
                return outcome
        return CommandOutcome(0)

    def argv_for(self, program: str) -> list[str] | None:
        for call in self.calls:
            if os.path.basename(call[0]) == program:
                return call
        return None


def _volume(fstype, path="/dev/sdb1"):
    return Volume(
        path=path,
        fstype=fstype,
        label=None,
        partlabel=None,
        size=1024,
        mountpoint=None,
    )


def test_a_fuse_helper_is_invoked_as_a_binary_not_through_mount(tmp_path):
    """The whole point of keeping the NTFS parse outside the kernel.

    `mount -t ntfs` would pick whichever helper happens to be installed, and apfs-fuse
    ships no `mount.<type>` helper for mount(8) to find at all.
    """
    runner = FakeRunner()
    mountpoint = str(tmp_path / "p1")

    mounted = mount_volume(_volume("ntfs"), mountpoint, UID, GID, KERNEL, runner)

    assert isinstance(mounted, MountedVolume)
    argv = runner.argv_for("ntfs-3g")
    assert argv is not None
    assert argv[0] == "ntfs-3g"
    assert argv[1] == "-o"
    assert argv[3:] == ["/dev/sdb1", mountpoint]
    assert runner.argv_for("mount") is None


def test_an_in_kernel_filesystem_goes_through_mount_with_its_type(tmp_path):
    runner = FakeRunner()
    mountpoint = str(tmp_path / "p1")

    mount_volume(_volume("ext4"), mountpoint, UID, GID, KERNEL, runner)

    argv = runner.argv_for("mount")
    assert argv is not None
    assert argv[:2] == ["mount", "-o"]
    assert "noload" in argv[2]
    assert argv[3:] == ["-t", "ext4", "/dev/sdb1", mountpoint]


def test_the_block_device_is_set_read_only_before_it_is_mounted(tmp_path):
    runner = FakeRunner()

    mount_volume(_volume("ext4"), str(tmp_path / "p1"), UID, GID, KERNEL, runner)

    programs = [os.path.basename(call[0]) for call in runner.calls]
    assert programs.index("blockdev") < programs.index("mount")
    assert runner.calls[0][:2] == ["blockdev", "--setro"]


def test_a_bridge_that_refuses_the_ioctl_does_not_stop_the_mount(tmp_path):
    """Some USB bridges reject `blockdev --setro`; the mount options still stand."""
    runner = FakeRunner({("blockdev",): CommandOutcome(1, "Inappropriate ioctl")})

    assert not set_block_read_only("/dev/sdb", runner)
    mounted = mount_volume(
        _volume("ext4"), str(tmp_path / "p1"), UID, GID, KERNEL, runner
    )

    assert isinstance(mounted, MountedVolume)


def test_a_corrupt_filesystem_is_skipped_with_what_mount_said(tmp_path):
    """The reason reaches the operator's console, so it has to be mount's own words."""
    runner = FakeRunner(
        {("mount",): CommandOutcome(32, "mount: wrong fs type, bad option\n")}
    )
    mountpoint = str(tmp_path / "p1")

    skipped = mount_volume(_volume("ext4"), mountpoint, UID, GID, KERNEL, runner)

    assert isinstance(skipped, SkippedVolume)
    assert skipped.reason == "mount: wrong fs type, bad option"
    # An empty directory left under the device's tree looks exactly like a mounted
    # volume to anything that walks it.
    assert not os.path.exists(mountpoint)


def test_a_mount_that_says_nothing_still_gives_a_reason(tmp_path):
    runner = FakeRunner({("mount",): CommandOutcome(1, "")})

    skipped = mount_volume(
        _volume("ext4"), str(tmp_path / "p1"), UID, GID, KERNEL, runner
    )

    assert isinstance(skipped, SkippedVolume)
    assert "1" in skipped.reason


def test_a_refused_volume_never_reaches_a_command(tmp_path):
    runner = FakeRunner()

    skipped = mount_volume(
        _volume("crypto_LUKS"), str(tmp_path / "p1"), UID, GID, KERNEL, runner
    )

    assert isinstance(skipped, SkippedVolume)
    assert not runner.calls


def test_unmount_falls_through_to_lazy_when_the_stick_was_pulled(tmp_path):
    """`umount` fails on a device that is gone; the mount must still go away.

    A stale mount left behind blocks the same device being ingested again later.
    """
    mountpoint = tmp_path / "p1"
    mountpoint.mkdir()
    runner = FakeRunner({("umount", str(mountpoint)): CommandOutcome(32, "busy")})

    unmount(str(mountpoint), runner)

    assert runner.calls == [
        ["umount", str(mountpoint)],
        ["umount", "--lazy", str(mountpoint)],
    ]
    assert not mountpoint.exists()


def test_unmount_stops_at_the_first_one_that_works(tmp_path):
    runner = FakeRunner()
    mountpoint = tmp_path / "p1"
    mountpoint.mkdir()

    unmount(str(mountpoint), runner)

    assert runner.calls == [["umount", str(mountpoint)]]
    assert not mountpoint.exists()
