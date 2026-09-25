"""The device interlock: what may be written to, and what may never be.

Every case here is one the installer has to get right on a box nobody can watch it
on. The list `target_disks` returns is not a menu -- every disk in it is partitioned
-- so a stick, a mounted disk or the medium the installer is running from appearing
in it is data loss, not a cosmetic bug.
"""

from fakes import FakeRunner

from loom_installer import constants, devices
from loom_installer.devices import KeyState

# Answered rather than restated: the fake box has to reply to the exact command
# `devices.py` asks, so it is imported from there.
LSBLK_DISKS = devices.LSBLK_WHOLE_DISKS


def with_stick(runner: FakeRunner, disk: str = "/dev/sda") -> FakeRunner:
    """A Loom stick, with all three of its labels on one device."""
    for index, label in enumerate(
        (constants.KEY_LABEL, constants.LIVE_STORE_LABEL, constants.LIVE_ESP_LABEL),
        start=1,
    ):
        partition = f"{disk}{index}"
        runner.links[f"{constants.BY_PARTLABEL}/{label}"] = partition
        runner.block_devices.add(partition)
        runner.succeeds(
            [
                "lsblk",
                "--noheadings",
                "--raw",
                "--paths",
                "--output",
                "PKNAME",
                partition,
            ],
            f"{disk}\n",
        )
    return runner


def with_internal_nvme(runner: FakeRunner, disk: str) -> FakeRunner:
    """An ordinary internal NVMe: not removable, not USB, nothing mounted."""
    runner.files[f"/sys/block/{disk.removeprefix('/dev/')}/removable"] = "0\n"
    runner.succeeds(
        ["udevadm", "info", "--query=property", f"--name={disk}"],
        "ID_MODEL=SAMSUNG\nID_BUS=nvme\n",
    )
    runner.succeeds(
        ["lsblk", "--noheadings", "--raw", "--paths", "--output", "MOUNTPOINTS", disk],
        "\n\n",
    )
    return runner


def test_the_boot_medium_is_resolved_from_our_own_labels() -> None:
    runner = with_stick(FakeRunner())
    assert devices.boot_disk(runner) == "/dev/sda"


def test_a_second_loom_stick_makes_the_boot_medium_unanswerable() -> None:
    # The labels resolve to two disks, and guessing which one we booted from is how
    # the wrong device gets erased. Every caller treats None as fatal.
    runner = with_stick(FakeRunner())
    runner.links[f"{constants.BY_PARTLABEL}/{constants.KEY_LABEL}"] = "/dev/sdb1"
    runner.block_devices.add("/dev/sdb1")
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
    assert devices.boot_disk(runner) is None


def test_no_labels_at_all_is_also_unanswerable() -> None:
    assert devices.boot_disk(FakeRunner()) is None


def test_only_internal_nvme_namespaces_are_targets() -> None:
    runner = with_stick(FakeRunner())
    runner.succeeds(
        LSBLK_DISKS,
        "\n".join(
            [
                "/dev/sda disk",  # the stick we booted from
                "/dev/sdb disk",  # somebody's external drive
                "/dev/nvme0n1 disk",
                "/dev/nvme0n1p1 part",  # not a disk
            ]
        ),
    )
    with_internal_nvme(runner, "/dev/nvme0n1")

    assert devices.target_disks(runner) == ["/dev/nvme0n1"]


def test_a_removable_or_usb_nvme_is_never_a_target() -> None:
    # A USB enclosure with an NVMe in it enumerates as sd*, but a Thunderbolt one
    # does not -- so neither check is redundant.
    runner = with_stick(FakeRunner())
    runner.succeeds(LSBLK_DISKS, "/dev/nvme0n1 disk\n/dev/nvme1n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")
    with_internal_nvme(runner, "/dev/nvme1n1")
    runner.files["/sys/block/nvme0n1/removable"] = "1\n"
    runner.succeeds(
        ["udevadm", "info", "--query=property", "--name=/dev/nvme1n1"],
        "ID_BUS=usb\n",
    )

    assert devices.target_disks(runner) == []


def test_an_unreadable_removable_flag_counts_as_removable() -> None:
    # The point of the check is to refuse when unsure.
    runner = with_stick(FakeRunner())
    runner.succeeds(LSBLK_DISKS, "/dev/nvme0n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")
    del runner.files["/sys/block/nvme0n1/removable"]

    assert devices.target_disks(runner) == []


def test_a_disk_with_something_mounted_is_the_live_system_not_a_target() -> None:
    runner = with_stick(FakeRunner())
    runner.succeeds(LSBLK_DISKS, "/dev/nvme0n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")
    runner.succeeds(
        [
            "lsblk",
            "--noheadings",
            "--raw",
            "--paths",
            "--output",
            "MOUNTPOINTS",
            "/dev/nvme0n1",
        ],
        "\n/mnt/data\n",
    )

    assert devices.target_disks(runner) == []


def test_an_nvme_we_booted_from_is_never_a_target() -> None:
    # A box booted off an internal disk rather than a stick: the medium the installer
    # is running from is excluded by identity, before any of the other rules.
    runner = with_stick(FakeRunner(), disk="/dev/nvme0n1")
    runner.succeeds(LSBLK_DISKS, "/dev/nvme0n1 disk\n/dev/nvme1n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")
    with_internal_nvme(runner, "/dev/nvme1n1")

    assert devices.target_disks(runner) == ["/dev/nvme1n1"]


def test_targets_come_back_sorted() -> None:
    # The order is load-bearing: the first disk gets the ESP and the NVRAM boot
    # entry, so it must not depend on what order lsblk happened to list them in.
    runner = with_stick(FakeRunner())
    runner.succeeds(LSBLK_DISKS, "/dev/nvme1n1 disk\n/dev/nvme0n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")
    with_internal_nvme(runner, "/dev/nvme1n1")

    assert devices.target_disks(runner) == ["/dev/nvme0n1", "/dev/nvme1n1"]


def test_an_unidentifiable_boot_medium_leaves_no_targets_at_all() -> None:
    # Not an empty list by accident: with nothing excluded, every internal disk would
    # be a target -- including the one the installer is running from.
    runner = FakeRunner()
    runner.succeeds(LSBLK_DISKS, "/dev/nvme0n1 disk\n")
    with_internal_nvme(runner, "/dev/nvme0n1")

    assert devices.target_disks(runner) == []


ZEROED = [
    "cmp",
    "--quiet",
    f"--bytes={constants.KEY_BYTES}",
    constants.KEY_DEVICE,
    "/dev/zero",
]
IS_CONTAINER = ["cryptsetup", "isLuks", "--type", "luks2", constants.KEY_DEVICE]


def test_key_state_distinguishes_missing_from_never_provisioned() -> None:
    runner = FakeRunner()
    assert devices.key_state(runner, constants.KEY_DEVICE, False) is KeyState.MISSING

    runner.block_devices.add(constants.KEY_DEVICE)
    # `cmp` against /dev/zero succeeding means the partition is all zeroes.
    runner.succeeds(ZEROED)
    assert devices.key_state(runner, constants.KEY_DEVICE, False) is KeyState.EMPTY

    runner.commands.clear()
    assert devices.key_state(runner, constants.KEY_DEVICE, False) is KeyState.PRESENT


def test_a_locked_stick_needs_a_container_rather_than_only_non_zero_bytes() -> None:
    # On a --lock-key stick the partition holds a LUKS2 header, so "not all zeroes"
    # would pass for any partition with anything on it at all -- including one a
    # previous unlocked flash left full of key bytes, which stage 1 would then try to
    # unlock and fail. Nothing else reports that, so it has to be caught here.
    runner = FakeRunner()
    runner.block_devices.add(constants.KEY_DEVICE)

    assert devices.key_state(runner, constants.KEY_DEVICE, True) is KeyState.EMPTY

    runner.succeeds(IS_CONTAINER)
    assert devices.key_state(runner, constants.KEY_DEVICE, True) is KeyState.PRESENT

    # An all-zero partition is EMPTY either way, and is answered before cryptsetup is
    # asked anything -- that is the one diagnosis that sends an operator to --flash.
    runner.commands.clear()
    runner.succeeds(ZEROED)
    assert devices.key_state(runner, constants.KEY_DEVICE, True) is KeyState.EMPTY


def test_nvme_serials_lose_their_padding() -> None:
    # NVMe pads Identify Controller fields to a fixed width, and every consumer of
    # this is a column on the operator's screen.
    runner = FakeRunner()
    runner.files["/sys/block/nvme0n1/device/model"] = "SAMSUNG MZVL2512   \n"
    runner.files["/sys/block/nvme0n1/device/serial"] = "  S6XSNU0T12345    \n"
    runner.succeeds(
        [
            "lsblk",
            "--nodeps",
            "--noheadings",
            "--raw",
            "--output",
            "SIZE",
            "/dev/nvme0n1",
        ],
        "476.9G\n",
    )

    disk = devices.describe_disk(runner, "/dev/nvme0n1")
    assert disk.model == "SAMSUNG MZVL2512"
    assert disk.serial == "S6XSNU0T12345"
    assert disk.describe() == "/dev/nvme0n1  SAMSUNG MZVL2512  SN S6XSNU0T12345  476.9G"


def test_an_absent_sysfs_attribute_reads_unknown_rather_than_blank() -> None:
    runner = FakeRunner()
    assert devices.sysfs_attr(runner, "/dev/nvme0n1", "serial") == "unknown"


def test_the_pool_is_measured_across_every_member() -> None:
    runner = FakeRunner()
    runner.succeeds(["blockdev", "--getsize64", "/dev/nvme0n1"], "500000000000\n")
    runner.succeeds(["blockdev", "--getsize64", "/dev/nvme1n1"], "500000000000\n")

    total = devices.pool_bytes(runner, ["/dev/nvme0n1", "/dev/nvme1n1"])
    assert total == 1000000000000


def test_a_disk_that_will_not_say_how_big_it_is_counts_as_nothing() -> None:
    # Which makes the pool too small and stops an unattended install, rather than
    # arming one against a disk nothing could measure.
    runner = FakeRunner()
    assert devices.pool_bytes(runner, ["/dev/nvme0n1"]) == 0
