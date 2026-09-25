"""Destroys the data on the box's internal disks.

Layered, cheapest-and-most-effective first. The data is LUKS-encrypted, so destroying
the key material IS the wipe; everything after layer 1 is defence in depth. Each layer
is allowed to fail -- an NVMe that refuses `nvme format` has still had its keyslots
erased.

A full overwrite is deliberately not the default: on a wear-levelling NVMe it takes
hours and still cannot reach retired or over-provisioned blocks, so it is both slower
and weaker than a controller-level sanitize.
"""

import argparse
import glob
import os
import signal
import sys

from loom_installer import constants, devices, storage
from loom_installer.commands import CommandError, CommandRunner, Subprocess
from loom_installer.console import (
    Aborted,
    Ui,
    build_ui,
    crash_handler,
    ignoring_interrupts,
)
from loom_installer.interlock import confirm_destructive
from loom_installer.settings import SettingsError, settings

# Enough to flatten a LUKS2 header, its keyslot area and the header backup that
# follows it.
HEADER_SCRUB_MB = 32


class WipeError(RuntimeError):
    """A precondition that makes wiping impossible or unsafe."""


def erase_pool_keys(runner: CommandRunner, ui: Ui | None = None) -> None:
    """Layer 1, and the only one that matters: destroy the key material.

    It lives on the logical volume rather than on a partition, so the per-partition
    sweep in `wipe_disk` below cannot reach it -- it would find no LUKS header, say
    nothing, and fall through to layers that are slower and weaker. The group has to be
    activated to erase what is inside it, and destroyed immediately after so the
    partition tables underneath are free.
    """
    root_device = settings().storage.root_device
    storage.release_storage(runner)
    storage.activate(runner)

    if (
        runner.is_block_device(root_device)
        and runner.run(["cryptsetup", "isLuks", root_device]).ok
    ):
        if ui is not None:
            ui.log(f"luksErase {root_device}")
        if not runner.run(["cryptsetup", "luksErase", "--batch-mode", root_device]).ok:
            if ui is not None:
                ui.warn(f"luksErase failed on {root_device}")
    elif ui is not None:
        # Not an error. A box installed by an older stick has its container on a
        # partition, which `wipe_disk` still sweeps; so does a disk that was never a
        # Loom box at all.
        ui.log("No pooled LUKS container found; the per-partition sweep still runs.")

    storage.discard_pool(runner)


def wipe_disk(runner: CommandRunner, ui: Ui, disk: str) -> None:
    """Layers 1 through 5 on one disk.

    Every one of them may fail.
    """
    ui.log(f"Wiping {devices.describe_disk(runner, disk).describe()}")
    partitions = _partitions_of(runner, disk)

    # Layer 1, continued: any container sitting directly on a partition. On a pooled
    # box `erase_pool_keys` has already dealt with the real one; this catches a disk
    # laid out by an older stick, or one that was never ours.
    for partition in partitions:
        if runner.run(["cryptsetup", "isLuks", partition]).ok:
            ui.log(f"  luksErase {partition}")
            if not runner.run(
                ["cryptsetup", "luksErase", "--batch-mode", partition]
            ).ok:
                ui.warn(f"  luksErase failed on {partition}")

    # Layer 2: flatten the headers themselves, including any keyslot cryptsetup did
    # not know about and the header backup area.
    for partition in partitions:
        runner.run(
            [
                "dd",
                "if=/dev/urandom",
                f"of={partition}",
                "bs=1M",
                f"count={HEADER_SCRUB_MB}",
                "oflag=direct",
                "conv=fsync",
                "status=none",
            ]
        )
        runner.run(["wipefs", "--all", partition])

    # Layer 3: partition table.
    runner.run(["sgdisk", "--zap-all", disk])
    runner.run(["wipefs", "--all", disk])

    # Layer 4: discard every block. -f drops the exclusive open that util-linux takes
    # by default.
    ui.log("  blkdiscard")
    if not runner.run(["blkdiscard", "-f", disk], timeout=3600).ok:
        ui.warn("  blkdiscard unsupported or refused; continuing")

    # Layer 5: ask the controller to erase. --ses=1 is a user-data erase, --ses=2 a
    # cryptographic one; not every drive implements either.
    ui.log("  nvme format")
    erased = (
        runner.run(["nvme", "format", disk, "--ses=1", "--force"], timeout=3600).ok
        or runner.run(["nvme", "format", disk, "--ses=2", "--force"], timeout=3600).ok
    )
    if not erased:
        ui.warn("  nvme format unsupported; layers 1-4 already applied")

    runner.run(["partprobe", disk])


def _partitions_of(runner: CommandRunner, disk: str) -> list[str]:
    """`/dev/nvme0n1p*`, and only the ones that are block devices right now."""
    return [
        candidate
        for candidate in sorted(glob.glob(f"{disk}p*"))
        if runner.is_block_device(candidate)
    ]


def run(runner: CommandRunner, ui: Ui) -> None:
    """The wipe, from preconditions to the last layer.

    Running as root is asked by `main` rather than here, the same way `install.run`
    does: it is a fact about this process rather than about this box.
    """
    boot = devices.boot_disk(runner)
    if boot is None:
        raise WipeError(
            "Could not identify the boot medium. Is a second Loom stick plugged in?"
        )

    targets = devices.target_disks(runner)
    if not targets:
        raise WipeError("No eligible internal NVMe found. Nothing to wipe.")

    confirm_destructive(ui, runner, "ERASE ALL DATA", boot, targets)

    # No teardown on the way out, unlike the install: the layers are ordered
    # most-effective-first and each one tolerates failing, so a wipe that stops part
    # way has destroyed key material and undone nothing. What it can leave behind is
    # the volume group `erase_pool_keys` activated to reach the container inside it,
    # and an active group keeps the partition tables busy -- which matters because the
    # menu's next option may be another wipe.
    try:
        erase_pool_keys(runner, ui)
        for disk in targets:
            wipe_disk(runner, ui, disk)
    except BaseException:
        with ignoring_interrupts():
            storage.deactivate(runner)
        ui.blank()
        ui.warn("Stopped part way. The keys may already be gone -- treat the data as")
        ui.warn("unrecoverable -- but the disks are not clean. Run Erase again.")
        raise

    ui.blank()
    ui.log("Wipe complete. The encryption keys are gone; the data is unrecoverable.")


def main(argv: list[str] | None = None) -> int:
    # First, and for the reason `install.main` gives: the menu ignores SIGINT while
    # this runs, and SIG_IGN is inherited across exec.
    signal.signal(signal.SIGINT, signal.default_int_handler)

    parser = argparse.ArgumentParser(
        prog="loom-wipe",
        description="Destroy the data on this box's internal disks.",
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])

    ui = build_ui()
    sys.excepthook = crash_handler(ui, constants.CRASH_LOG)

    if os.geteuid() != 0:
        ui.warn("The wipe must run as root.")
        return 1

    try:
        run(Subprocess(), ui)
    except Aborted as error:
        # Before the tuple below: `Aborted` and `WipeError` are both RuntimeErrors.
        ui.warn(str(error))
        return constants.EXIT_CANCELLED
    except KeyboardInterrupt:
        ui.warn("Cancelled.")
        return constants.EXIT_CANCELLED
    except (WipeError, CommandError, SettingsError, OSError) as error:
        ui.warn(str(error))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
