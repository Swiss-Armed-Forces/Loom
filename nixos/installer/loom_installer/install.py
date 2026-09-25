"""Installs the Loom appliance onto the box's internal NVMe.

Everything installed here is already on the stick, so this never touches the network:
the appliance closure rides along in the `loom-live-store` partition and nixos-install
only has to copy it.

The steps are module-level functions taking the runner and their arguments, and not
methods on some Installer object, for one reason: nixos/tests/appliance-install.nix
drives `partition`, `create_pool`, `encrypt`, `make_filesystems`, `mount_target` and
`enroll_recovery_passphrase` one at a time against scratch disks. That test is the only
thing standing between a change to the layout below and a box that installs perfectly
and then cannot find its own root.
"""

import argparse
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import StrEnum

from rich.table import Table
from rich.text import Text

from loom_installer import constants, devices, keystore, storage
from loom_installer.commands import CommandError, CommandRunner, Subprocess
from loom_installer.console import (
    Aborted,
    Ui,
    build_ui,
    crash_handler,
    ignoring_interrupts,
)
from loom_installer.devices import KeyState
from loom_installer.interlock import confirm_destructive
from loom_installer.keystore import KeystoreError
from loom_installer.progress import CopyProgress
from loom_installer.settings import Settings, SettingsError, settings

# Six groups of five. Plenty of entropy and still transcribable by someone reading
# it off a monitor; the alphabet has no character that can be misread as another.
PASSPHRASE_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
PASSPHRASE_GROUPS = 6
PASSPHRASE_GROUP_LENGTH = 5


class InstallError(RuntimeError):
    """A precondition that makes installing impossible or unsafe."""


class Degradation(StrEnum):
    """Something that succeeded well enough to finish, but not to be silent about."""

    # The firmware will not reach the internal disk at all. The menu answers this
    # by telling the operator to fix the firmware boot order.
    BOOT_ORDER = "boot-order"
    # The disk boots fine and merely starts on the wrong entry, where that advice
    # would be wrong. Reported in the completion block instead.
    SETUP_ENTRY = "setup-entry"


@dataclass
class InstallReport:
    """What the install did, for the completion block and for the exit status."""

    passphrase: str = ""
    degraded: set[Degradation] = field(default_factory=set)


def check_pool_size(runner: CommandRunner, disks: list[str]) -> None:
    """Refuse a pool nothing useful fits in.

    Documentation/installation.md asks for 200 GiB, and the container images alone are
    around 60 GB. Measured across the pool, because that is what the box actually gets.
    """
    total = devices.pool_bytes(runner, disks)
    if total < constants.MIN_POOL_BYTES:
        raise InstallError(
            f"{len(disks)} disk(s) totalling {total // constants.GIGABYTE} GB;"
            f" Loom needs at least {constants.MIN_POOL_BYTES // constants.GIGABYTE} GB."
        )


def partition(runner: CommandRunner, disks: list[str], ui: Ui | None = None) -> None:
    """Lay out every disk that will join the pool.

    The first one carries the ESP as well, because the firmware has to be pointed at
    exactly one loader and a second copy would only ever go stale. Losing that disk
    loses the box either way -- a linear pool has no redundancy -- so nothing is gained
    by spreading the boot partition around.
    """
    # Anything still holding these disks -- a pool from a previous install, its LUKS
    # mapping -- has to go first, or sgdisk finds the device busy and the install
    # dies with the disks in a worse state than it found them.
    storage.discard_pool(runner)

    for index, disk in enumerate(disks):
        if ui is not None:
            ui.log(f"Partitioning {disk}")

        runner.check(["wipefs", "--all", disk])
        runner.check(["sgdisk", "--zap-all", disk])

        # 8e00 is "Linux LVM". The pool member is a partition rather than the whole
        # disk so that the GPT keeps saying what the space is for.
        pv_label = f"{constants.PV_LABEL_PREFIX}{index}"
        if index == 0:
            runner.check(
                [
                    "sgdisk",
                    "--new=1:0:+1G",
                    "--typecode=1:ef00",
                    f"--change-name=1:{constants.ESP_LABEL}",
                    "--new=2:0:0",
                    "--typecode=2:8e00",
                    f"--change-name=2:{pv_label}",
                    disk,
                ]
            )
        else:
            runner.check(
                [
                    "sgdisk",
                    "--new=1:0:0",
                    "--typecode=1:8e00",
                    f"--change-name=1:{pv_label}",
                    disk,
                ]
            )

        runner.check(["partprobe", disk])

    runner.check(["udevadm", "settle"])


def create_pool(runner: CommandRunner, count: int, ui: Ui | None = None) -> None:
    """One volume group across every member, and one logical volume filling it.

    Linear allocation, deliberately: `--stripes` would cap the pool at N times the
    smallest disk, and the two M.2 slots on a box are not required to hold matching
    drives. Concatenation uses every extent of both.
    """
    config = settings()
    physical_volumes = [
        f"{constants.BY_PARTLABEL}/{constants.PV_LABEL_PREFIX}{index}"
        for index in range(count)
    ]

    if ui is not None:
        ui.log(
            f"Pooling {count} disk(s) into volume group {config.storage.volume_group}"
        )

    runner.check(["pvcreate", "--force", "--yes", *physical_volumes])
    runner.check(["vgcreate", config.storage.volume_group, *physical_volumes])
    runner.check(
        [
            "lvcreate",
            "--yes",
            "--extents",
            "100%FREE",
            "--name",
            config.storage.root_volume,
            config.storage.volume_group,
        ]
    )
    runner.check(["udevadm", "settle"])


def encrypt(runner: CommandRunner, key_device: str, ui: Ui | None = None) -> None:
    """The LUKS2 container, on the logical volume.

    pbkdf2 with a low iteration count is deliberate: the key is 4096 bytes of
    /dev/urandom, so stretching it buys nothing and only slows every boot. That
    argument holds whichever kind of stick this is -- `--lock-key` changes what
    guards those bytes, not what they are, and its own container is the one that
    takes a human passphrase and is formatted with argon2id to match
    (cicd/build_appliance_image.sh `write_key_partition`).
    """
    root_device = settings().storage.root_device
    if ui is not None:
        ui.log("Creating the LUKS2 container")

    runner.check(
        [
            "cryptsetup",
            "luksFormat",
            "--type",
            "luks2",
            "--batch-mode",
            "--pbkdf",
            "pbkdf2",
            "--pbkdf-force-iterations",
            "1000",
            "--key-size",
            "512",
            "--cipher",
            "aes-xts-plain64",
            "--key-file",
            key_device,
            "--keyfile-size",
            str(constants.KEY_BYTES),
            root_device,
        ]
    )
    runner.check(
        [
            "cryptsetup",
            "open",
            "--key-file",
            key_device,
            "--keyfile-size",
            str(constants.KEY_BYTES),
            root_device,
            constants.CRYPT_MAPPING,
        ]
    )


def make_filesystems(runner: CommandRunner, ui: Ui | None = None) -> None:
    if ui is not None:
        ui.log("Creating filesystems")
    runner.check(
        [
            "mkfs.vfat",
            "-F",
            "32",
            "-n",
            "LOOMESP",
            f"{constants.BY_PARTLABEL}/{constants.ESP_LABEL}",
        ]
    )
    runner.check(
        ["mkfs.ext4", "-q", "-L", "loomroot", f"/dev/mapper/{constants.CRYPT_MAPPING}"]
    )


def mount_target(runner: CommandRunner) -> None:
    """The live root is a tmpfs built from nothing, so /mnt does not exist until we
    create it -- unlike on an installed system, where it always does.

    The ESP is mounted with the same `umask=0077` box-hardware.nix gives it, because
    vfat has no permissions on disk and synthesises every mode from the mount options.
    nixos-install's bootloader step writes /boot/loader/random-seed through this mount,
    and bootctl warns that the seed is world accessible when the mount it lands on is
    0022. Nothing is left insecure without this -- the installed box remounts the same
    partition at 0077 -- but the warning is the last thing an operator sees at the end
    of an install, and it should not be there.
    """
    os.makedirs(constants.MOUNT, exist_ok=True)
    runner.check(["mount", f"/dev/mapper/{constants.CRYPT_MAPPING}", constants.MOUNT])
    os.makedirs(f"{constants.MOUNT}/boot", exist_ok=True)
    runner.check(
        [
            "mount",
            "-o",
            constants.ESP_MOUNT_OPTIONS,
            f"{constants.BY_PARTLABEL}/{constants.ESP_LABEL}",
            f"{constants.MOUNT}/boot",
        ]
    )


def unmount_target(runner: CommandRunner) -> None:
    runner.check(["umount", "--recursive", constants.MOUNT])
    runner.check(["cryptsetup", "close", constants.CRYPT_MAPPING])
    # The group outlives the mapping, and an active one keeps the partition tables
    # busy -- which matters because the menu is still running and its next option
    # may be a wipe.
    storage.deactivate(runner)


def install_system(runner: CommandRunner, ui: Ui) -> None:
    """Copy the appliance closure onto the freshly mounted root.

    `--system` installs a pre-built closure, so nothing is evaluated or built.
    nixos-install still shells out to `nix-env --extra-substituters
    'auto?trusted=1'` regardless, so the substituters are emptied explicitly as well
    -- otherwise a store hiccup becomes a hang on a box with no network rather than
    a clean failure.

    This is the long step -- tens of gigabytes onto an NVMe -- and the one the
    operator is standing there watching, so it is the one with a progress bar. The
    bar is driven by how full the target filesystem is, because that is the only
    measure of this that exists: nixos-install reports paths, not bytes, and the
    number of paths left is not knowable from outside it. Its output is printed
    above the bar rather than swallowed, because a failed install with no visible
    reason is the worst thing that can happen on media whose whole job is being
    diagnosable by whoever is standing at the box.
    """
    system = (runner.read_text(constants.TARGET_SYSTEM_FILE) or "").strip()
    if not system:
        raise InstallError(f"{constants.TARGET_SYSTEM_FILE} is empty or missing.")

    ui.log(f"Installing {system}")

    with CopyProgress(ui, constants.MOUNT, _closure_bytes(runner, system)) as progress:
        _stream(
            [
                "nixos-install",
                "--root",
                constants.MOUNT,
                "--system",
                system,
                "--no-channel-copy",
                "--no-root-password",
                "--option",
                "substituters",
                "",
                "--option",
                "builders",
                "",
                "--option",
                "connect-timeout",
                "1",
            ],
            progress,
        )


def _closure_bytes(runner: CommandRunner, system: str) -> int | None:
    """How much there is to copy, or None when nix will not say.

    Asked of the Nix database rather than measured off the squashfs: `--size` is the
    NAR size recorded for each path, so the answer costs two queries instead of a
    traversal of every file in the closure. It is an approximation of what lands on
    ext4, which is all a bar needs.

    None is not a failure: the progress display falls back to a spinner and the
    install is unaffected.
    """
    requisites = runner.output(
        ["nix-store", "--query", "--requisites", system], timeout=120
    )
    paths = [line.strip() for line in requisites.splitlines() if line.strip()]
    if not paths:
        return None

    sizes = runner.output(["nix-store", "--query", "--size", *paths], timeout=120)
    total = 0
    for line in sizes.split():
        try:
            total += int(line)
        except ValueError:
            continue
    return total or None


def _stream(argv: list[str], progress: CopyProgress) -> None:
    """Run a command, printing its output above the progress display.

    The kill on the way out is not tidiness. This is the longest step of the install and
    therefore where a Ctrl-C actually lands, and `Popen.__exit__` deliberately does not
    reap a child it was interrupted out of -- it waits a quarter second and returns. A
    `nixos-install` that outlives the interrupt holds /mnt, and then the teardown in
    `run` below cannot unmount it and the box is left worse than if nothing had been
    attempted.
    """
    with subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    ) as process:
        assert process.stdout is not None
        try:
            for line in process.stdout:
                progress.log(line.rstrip())
            returncode = process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise

    if returncode != 0:
        raise InstallError(f"{argv[0]} failed with exit status {returncode}.")


def select_setup_entry(runner: CommandRunner, ui: Ui, report: InstallReport) -> None:
    """Leave the boot menu pointing at first-time setup.

    A fresh box has no container images, so the first boot has to be the
    `Loom (first-time-setup)` entry -- see nixos/modes.nix. Selecting it here is not
    merely a convenience: the default `Loom` entry serves DHCP and wildcard *.loom on
    the appliance NIC, so a box that boots it while still cabled to the network it
    fetches over puts a DHCP server on that network. Choosing correctly every time is
    not something to leave to whoever is watching the menu.

    Written by hand rather than by re-running the bootloader builder, because the
    builder cannot express it. It decides which entry is default by comparing its
    DEFAULT-CONFIG argument against the *main* toplevel only, and then calls
    write_loader_conf() with no specialisation -- so `default` can never name
    anything but `nixos-generation-<N>.conf`.

    The line stays put because nothing regenerates it: the installed box has no
    nixos-rebuild, no channel and no evaluation. `loom-promote-boot-entry`
    (modes.nix) is what rewrites it, once, at the end of the setup run.

    Every failure below warns and returns. The disk is partitioned, encrypted and
    written by this point, and the fallback is exactly the behaviour this step
    replaces -- an operator picking the entry off the menu themselves.
    """
    conf = f"{constants.MOUNT}/boot/loader/loader.conf"
    entries = f"{constants.MOUNT}/boot/loader/entries"
    specialisation = (
        runner.read_text(constants.SETUP_SPECIALISATION_FILE) or ""
    ).strip()

    loader = runner.read_text(conf)
    if loader is None:
        ui.warn(f"No {conf} after install; cannot preselect first-time setup.")
        report.degraded.add(Degradation.SETUP_ENTRY)
        return

    # What nixos-install just wrote: `default nixos-generation-<N>.conf`. Read rather
    # than assumed, so the generation number comes from the file -- it is 1 on a
    # freshly mkfs'd root, but nothing here needs to depend on that.
    current = default_entry(loader)
    if current is None:
        ui.warn(f"No 'default' line in {conf}; cannot preselect first-time setup.")
        report.degraded.add(Degradation.SETUP_ENTRY)
        return

    # The filename the systemd-boot builder composes for a specialisation, per its
    # own generation_conf_filename(): the generation's entry, with the
    # specialisation's attribute name appended.
    setup = f"{current.removesuffix('.conf')}-specialisation-{specialisation}.conf"

    # Checked before anything is rewritten. This is what catches a renamed or removed
    # specialisation, and it is why the specialisation file is written from the
    # evaluated configuration rather than spelled out here.
    if not os.path.isfile(f"{entries}/{setup}"):
        ui.warn(f"Expected {setup} in {entries}, but it is not there.")
        report.degraded.add(Degradation.SETUP_ENTRY)
        return

    # Only the default line. `timeout`, `editor` and `console-mode` stay exactly as
    # the builder wrote them.
    rewritten = re.sub(r"(?m)^default .*$", f"default {setup}", loader, count=1)
    with open(conf, "w", encoding="utf-8") as handle:
        handle.write(rewritten)

    if default_entry(runner.read_text(conf) or "") != setup:
        ui.warn(f"Could not select {setup} in {conf}.")
        report.degraded.add(Degradation.SETUP_ENTRY)
        return

    ui.log("First-time setup is the default boot entry")


def default_entry(loader_conf: str) -> str | None:
    """The entry `loader.conf` currently selects, or None when it selects nothing.

    Read rather than assumed all through `select_setup_entry`: the generation number
    comes from the file, and a loader.conf the builder wrote differently is a case that
    warns instead of one that rewrites the wrong line.
    """
    for line in loader_conf.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == "default":
            return fields[1]
    return None


def generate_passphrase() -> str:
    """A recovery passphrase somebody can read off a monitor and type back in."""
    groups = [
        "".join(
            secrets.choice(PASSPHRASE_ALPHABET) for _ in range(PASSPHRASE_GROUP_LENGTH)
        )
        for _ in range(PASSPHRASE_GROUPS)
    ]
    return "-".join(groups)


def enroll_recovery_passphrase(runner: CommandRunner, key_device: str) -> str:
    """Add a second keyslot, and leave the passphrase on the installed root.

    Generated here rather than at image build time, so it never leaves the box and
    every box gets its own.

    Takes the key device rather than naming the partition itself, as `encrypt` above
    already does: the two have to unlock the same container with the same bytes, and
    one of them reaching for a path of its own is how they would stop.
    """
    passphrase = generate_passphrase()
    target = os.path.join(constants.MOUNT, constants.RECOVERY_FILE_REL)

    # A pipe rather than the process substitution the shell used: the passphrase
    # never becomes a path in /proc anywhere, and there is no file to leave behind.
    runner.check(
        [
            "cryptsetup",
            "luksAddKey",
            "--key-file",
            key_device,
            "--keyfile-size",
            str(constants.KEY_BYTES),
            "--batch-mode",
            settings().storage.root_device,
            "-",
        ],
        stdin=passphrase,
    )

    # Safe to store in the clear: reading it requires the disk to be unlocked and
    # mounted, which already requires the stick or this very passphrase.
    os.makedirs(os.path.dirname(target), mode=0o750, exist_ok=True)
    os.chmod(os.path.dirname(target), 0o750)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(f"{passphrase}\n")
    os.chmod(target, 0o440)
    # root:wheel -- wheel is gid 1 on NixOS, and /etc/group is not readable from
    # here in a way worth parsing.
    os.chown(target, 0, 1)

    return passphrase


def fix_boot_order(
    runner: CommandRunner, ui: Ui, report: InstallReport, esp_disk: str, boot: str
) -> None:
    """Point the firmware at the internal disk, and take the stick off the fallback.

    The stick stays plugged in forever and carries the UEFI removable-media fallback
    path, so most firmware would boot the installer on every reboot. Give the internal
    disk a named NVRAM entry and move the stick's loader aside, leaving it reachable
    from the firmware's own boot menu.
    """
    efi_arch = settings().efi_arch
    ui.log("Making the internal disk the default boot entry")

    # efibootmgr does not check that the loader exists, so a wrong name here produces
    # an entry the firmware silently cannot boot.
    created = runner.run(
        [
            "efibootmgr",
            "--create",
            "--disk",
            esp_disk,
            "--part",
            "1",
            "--loader",
            f"\\EFI\\systemd\\systemd-boot{efi_arch}.efi",
            "--label",
            "Loom appliance",
        ]
    )
    if not created.ok:
        ui.warn(
            "Could not create an NVRAM boot entry."
            " Select the internal disk manually in firmware."
        )
        report.degraded.add(Degradation.BOOT_ORDER)
        return

    _move_stick_fallback(runner, ui, report, boot)


def _move_stick_fallback(
    runner: CommandRunner, ui: Ui, report: InstallReport, boot: str
) -> None:
    efi_arch = settings().efi_arch
    mountpoint = tempfile.mkdtemp(prefix="loom-stick-esp.")

    try:
        mounted = runner.run(
            [
                "mount",
                f"{constants.BY_PARTLABEL}/{constants.LIVE_ESP_LABEL}",
                mountpoint,
            ]
        )
        if not mounted.ok:
            # Until this was reported it was the one way to reach the consequence
            # below in silence: an unmountable stick ESP left the fallback loader in
            # place with nothing printed about it.
            ui.warn(
                f"Could not mount the stick's {constants.LIVE_ESP_LABEL} partition."
            )
            _warn_stick_owns_fallback(ui, report)
            return

        try:
            fallback = f"{mountpoint}/EFI/BOOT/BOOT{efi_arch.upper()}.EFI"
            if not os.path.isfile(fallback):
                # Not cosmetic: the stick stays plugged in forever, so as long as it
                # owns the removable-media path most firmware boots the installer
                # instead of the appliance on every restart.
                ui.warn(f"Expected {fallback} on the stick, but it is not there.")
                _warn_stick_owns_fallback(ui, report)
                return

            os.makedirs(f"{mountpoint}/EFI/loom", exist_ok=True)
            os.replace(fallback, f"{mountpoint}/EFI/loom/boot{efi_arch}.efi")
            ui.log(
                f"Installer moved to \\EFI\\loom\\boot{efi_arch}.efi on {boot};"
                " reach it from the firmware boot menu."
            )
        finally:
            runner.run(["umount", mountpoint])
    finally:
        try:
            os.rmdir(mountpoint)
        except OSError:
            pass


def _warn_stick_owns_fallback(ui: Ui, report: InstallReport) -> None:
    ui.warn("The stick still owns the UEFI removable-media path, so this box may boot")
    ui.warn(
        "the installer again. Put the internal disk first in the firmware boot order."
    )
    report.degraded.add(Degradation.BOOT_ORDER)


def run(runner: CommandRunner, ui: Ui, auto: bool) -> InstallReport:
    """The install, from preconditions to completion block.

    `auto` skips the typed interlock and nothing else -- every refusal below still
    applies, because an unattended install is exactly when a bad precondition must stop
    the run rather than be confirmed away.

    The one refusal that is not here is running as root, which `main` asks instead: it
    is a fact about this process rather than about this box, and leaving it here is what
    made everything below unreachable from a test that is not running as root.
    """
    boot = devices.boot_disk(runner)
    if boot is None:
        raise InstallError(
            "Could not identify the boot medium. Is a second Loom stick plugged in?"
        )

    targets = devices.target_disks(runner)
    if not targets:
        raise InstallError("No eligible internal NVMe found. Nothing to install onto.")

    check_pool_size(runner, targets)

    config = settings()
    state = devices.key_state(runner, constants.KEY_DEVICE, config.key_store.locked)
    if state is not KeyState.PRESENT:
        raise InstallError(
            f"The {constants.KEY_LABEL} partition is {state}."
            " Re-flash with 'build-appliance-image --flash'."
        )

    # Before the interlock, and before anything is written. On a `--lock-key` stick
    # this prompts, and a mistyped passphrase should cost an operator nothing -- the
    # same mistake discovered after `partition` would leave a box with no pool and no
    # way to make one. On an ordinary stick it is not even a prompt: `unlocked_key`
    # yields the key partition and does nothing else.
    with keystore.unlocked_key(runner, ui) as key_device:
        if not auto:
            confirm_destructive(ui, runner, "INSTALL", boot, targets)

        report = InstallReport()

        # From here the disks are being written to, and every way out of this block
        # leaves a box that cannot boot. The guard is inside `unlocked_key` so that
        # closing the stick's key mapping stays the outermost teardown, and after the
        # interlock so that declining it is still just a refusal -- nothing has been
        # written at that point and the operator must not be told otherwise.
        #
        # `BaseException` rather than the two cancellations: an sgdisk that fails
        # leaves the box in exactly the same state as a Ctrl-C, and saying so is the
        # whole point of the block.
        try:
            partition(runner, targets, ui)
            create_pool(runner, len(targets), ui)
            encrypt(runner, key_device, ui)
            make_filesystems(runner, ui)
            mount_target(runner)
            install_system(runner, ui)
            select_setup_entry(runner, ui, report)
            report.passphrase = enroll_recovery_passphrase(runner, key_device)
            # targets[0]: the ESP lives on the first pool member, and that is the
            # disk the firmware has to be pointed at.
            fix_boot_order(runner, ui, report, targets[0], boot)
            unmount_target(runner)
        except BaseException:
            _abandon_disks(runner, ui)
            raise

    _completion_block(ui, report, config)
    return report


def _abandon_disks(runner: CommandRunner, ui: Ui) -> None:
    """Let go of a half-written box, and say out loud what it now is.

    Letting go matters because the menu is still running and its next option may be a
    wipe: a mounted /mnt, an open dm-crypt mapping or an active volume group all keep
    the partition tables busy. `release_storage` is the same call both destructive paths
    already begin with, so this leaves the box in the state a retry expects.

    Saying so matters more. The install is the one operation here that is not atomic,
    and "Installation failed." on its own reads like nothing happened.
    """
    with ignoring_interrupts():
        storage.release_storage(runner)

    # Outside the guard above: a second Ctrl-C may skip the text, which costs nothing,
    # but must not land in the middle of the commands.
    ui.blank()
    ui.warn("The internal disks have already been written to. This box will NOT boot.")
    ui.warn("Run Install again, or Erase, before using this box.")


def _completion_block(ui: Ui, report: InstallReport, config: Settings) -> None:
    ui.blank()
    ui.log("Installation complete.")
    ui.blank()

    recovery = Table.grid(padding=(0, 1))
    recovery.add_column(overflow="fold")
    recovery.add_row(Text(report.passphrase, style="loom.brand"))
    recovery.add_row("")
    recovery.add_row("Write this down now and keep it somewhere other than the box.")
    recovery.add_row("Without the USB stick it is the only way to unlock this disk.")
    recovery.add_row("It is also shown on every console login.")
    if config.key_store.locked:
        # Worth saying out loud on a locked stick, because it is the one way back
        # in that the passphrase over the key does not cover. Somebody who reads
        # this off the screen holds a single-factor unlock for the life of the box.
        recovery.add_row("")
        recovery.add_row("This works on its own -- no stick, no stick passphrase.")
    ui.show(ui.panel(recovery, "LUKS recovery passphrase", style="loom.warn"))
    ui.blank()

    ui.log("Leave the USB stick plugged in. The box cannot boot without it, and")
    ui.log("removing it from a running box powers that box off ten seconds later.")
    if config.key_store.locked:
        ui.log("This stick's key is passphrase-locked, so every boot stops and asks")
        ui.log("for that passphrase. The box cannot come up unattended.")
    ui.blank()

    # What happens next, because nothing else says it: this box needs one boot on a
    # network with internet before it is of any use offline.
    if Degradation.SETUP_ENTRY in report.degraded:
        ui.warn("Could not preselect the first-time-setup entry -- see above.")
        ui.warn("At the boot menu, choose 'Loom (first-time-setup)' by hand.")
    else:
        ui.log("This box boots into first-time setup by itself. Leave it on a network")
        ui.log("with internet until it powers itself off; that run pulls every")
        ui.log("container image, and it never needs the internet again afterwards.")

    ui.note(f"  {config.platform} -- {config.tag}")


def main(argv: list[str] | None = None) -> int:
    # First, and load-bearing: the menu ignores SIGINT while this runs, and SIG_IGN is
    # inherited across exec. Without this line Ctrl-C never reaches this process at all
    # and none of the handling below can happen. See menu.run_install.
    signal.signal(signal.SIGINT, signal.default_int_handler)

    parser = argparse.ArgumentParser(
        prog="loom-install", description="Install the Loom appliance onto this box."
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="skip the typed confirmation; the menu passes this once it has counted"
        " down, and nothing else does",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    ui = build_ui()
    sys.excepthook = crash_handler(ui, constants.CRASH_LOG)
    runner = Subprocess()

    if os.geteuid() != 0:
        ui.warn("The installer must run as root.")
        return 1

    try:
        report = run(runner, ui, auto=args.auto)
    except Aborted as error:
        # Before the tuple below, which would otherwise swallow it: `Aborted` is a
        # RuntimeError, and so is `InstallError`.
        ui.warn(str(error))
        return constants.EXIT_CANCELLED
    except KeyboardInterrupt:
        # Ctrl-C somewhere that is not a prompt. Returned rather than re-raised under
        # the default handler, because dying of SIGINT would reach the menu as
        # `returncode == -2` -- a second spelling of the same thing for it to learn.
        ui.warn("Cancelled.")
        return constants.EXIT_CANCELLED
    except (
        InstallError,
        CommandError,
        KeystoreError,
        SettingsError,
        OSError,
    ) as error:
        ui.warn(str(error))
        return 1

    if Degradation.BOOT_ORDER in report.degraded:
        return constants.EXIT_BOOT_ORDER_DEGRADED
    return 0


if __name__ == "__main__":
    sys.exit(main())
