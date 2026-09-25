"""The installer's console menu, on tty1.

This is a TUI rather than extra bootloader entries on purpose: a boot menu cannot
enumerate disks, so it could never show the operator which drive is about to be
destroyed, and firmware differs wildly in how it renders menus and accepts input. A
program on a Linux console behaves the same everywhere.
"""

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import NamedTuple

from rich.table import Table
from rich.text import Text

from loom_installer import constants, devices, storage
from loom_installer.commands import CommandRunner, Subprocess
from loom_installer.console import (
    Aborted,
    Keypress,
    Ui,
    build_ui,
    console_restored,
    crash_handler,
    ignoring_interrupts,
)
from loom_installer.decision import (
    AutoInstall,
    AutoInstallInputs,
    BootState,
    decide,
    decide_boot_state,
    reason,
)
from loom_installer.devices import KeyState
from loom_installer.settings import SettingsError, settings

# How long a finished install holds the console before rebooting itself.
#
# Shorter than modes.nix's 60s poweroff grace on purpose, and not drift: that one
# has to be read by whoever happens to walk past, while this screen is only ever
# reached by an operator who just typed INSTALL and is standing there. 30s is enough
# to copy down a 30-character passphrase, and enter cuts it short.
REBOOT_GRACE_S = 30


class Choice(StrEnum):
    """What the operator can pick, by the key they press."""

    INSTALL = "1"
    WIPE = "2"
    REBOOT = "3"
    POWEROFF = "4"
    RESCUE = "5"


# The rescue shell stays the default: it is the one option that cannot destroy
# anything, so an idle keypress lands somewhere harmless. Both destructive options
# additionally run the interlock in interlock.py, which demands the action word.
DEFAULT_CHOICE = Choice.RESCUE


class MenuEntry(NamedTuple):
    """One line of the menu."""

    label: str
    style: str


# Only the destructive option is coloured. Ranking works by contrast: paint every
# line and none of them stands out.
ENTRIES: dict[Choice, MenuEntry] = {
    Choice.INSTALL: MenuEntry("Install Loom appliance to the internal disks", ""),
    Choice.WIPE: MenuEntry("ERASE ALL DATA on the internal disks", "loom.danger"),
    Choice.REBOOT: MenuEntry("Reboot", ""),
    Choice.POWEROFF: MenuEntry("Power off", ""),
    Choice.RESCUE: MenuEntry("Rescue shell", "loom.quiet"),
}


@dataclass(frozen=True)
class BoxState:
    """Everything the status block shows and the auto-install rule decides on.

    Gathered once per pass round the menu loop, because gathering it twice would mean
    probing the disks twice for one screen.
    """

    boot: str | None
    key_state: KeyState
    targets: list[str]
    pool_bytes: int
    verdict: AutoInstall


def inspect(runner: CommandRunner) -> BoxState:
    key_locked = settings().key_store.locked
    boot = devices.boot_disk(runner)
    key_state = devices.key_state(runner, constants.KEY_DEVICE, key_locked)
    targets = devices.target_disks(runner)
    pool_bytes = devices.pool_bytes(runner, targets)
    boot_state = decide_boot_state(
        attempted=os.path.exists(constants.AUTO_MARKER),
        declined=os.path.exists(constants.AUTO_DECLINED),
    )

    # Only probed when the answer could change anything. The check activates a
    # volume group and opens a LUKS header: meaningless without a key and a disk,
    # and worse than meaningless once an install has been attempted this boot,
    # because then it would be reading a disk that is part way through being
    # written.
    #
    # A declined countdown is there for neither reason: nothing on the disks has
    # changed, but the answer cannot change the verdict either, and the probe costs
    # an activated volume group and an opened LUKS header for nothing.
    #
    # `key_locked` is the hardest reason not to ask: the probe
    # unlocks the root with the stick's key bytes, and on a locked stick those are
    # behind a passphrase nobody has typed yet. There is nothing to lose by
    # skipping it, because a locked key refuses the unattended install outright
    # (decision.py) and the probe exists only to gate that install.
    claimed = False
    if (
        boot_state is BootState.FRESH
        and not key_locked
        and targets
        and key_state is KeyState.PRESENT
    ):
        claimed = storage.pool_claimed_by_key(runner, constants.KEY_DEVICE)

    return BoxState(
        boot=boot,
        key_state=key_state,
        targets=targets,
        pool_bytes=pool_bytes,
        verdict=decide(
            AutoInstallInputs(
                boot_state=boot_state,
                boot_disk=boot,
                key_state=key_state,
                key_locked=key_locked,
                target_count=len(targets),
                pool_bytes=pool_bytes,
                claimed=claimed,
            )
        ),
    )


def show_status(ui: Ui, runner: CommandRunner, state: BoxState) -> None:
    """The header: the mark, what this stick is, and what it is looking at."""
    # Drawn from the top each time round the loop, so the menu is never buried under
    # the scroll of whatever ran before it. `main` puts its "press enter" after an
    # install or a wipe, which is what keeps their output readable until the
    # operator has actually read it.
    ui.clear()
    ui.blank()
    ui.banner()

    config = settings()
    # Names the release and the box this stick was built for. Two sticks on a desk
    # are otherwise indistinguishable, and the only other place that information
    # exists is the banner on an already-installed box. The eyes above are the mark,
    # not the name, so this line still carries it.
    ui.blank()
    ui.show(
        Text("  LOOM APPLIANCE INSTALLER  ", style="loom.head").append(
            config.tag, style="loom.brand"
        )
    )
    ui.show(Text(f"  {config.platform}", style="loom.quiet"))
    ui.rule()

    table = ui.status_table()

    if state.boot is not None:
        table.add_row(
            "Boot medium", devices.describe_disk(runner, state.boot).describe()
        )
        table.add_row(
            "", Text("(never written to by any option below)", style="loom.quiet")
        )
    else:
        table.add_row(
            "Boot medium", Text("COULD NOT BE IDENTIFIED", style="loom.danger")
        )
        table.add_row("", "Install and wipe will refuse to run.")

    if state.key_state is KeyState.PRESENT:
        if settings().key_store.locked:
            # Said here rather than only at the prompt, because it is also the
            # explanation for the missing countdown two rows down.
            table.add_row(
                "LUKS key", Text("present, passphrase-locked", style="loom.ok")
            )
        else:
            table.add_row("LUKS key", Text("present", style="loom.ok"))
    else:
        # Not cosmetic: installing on a stick with no key produces a box that
        # partitions, encrypts, and then never boots again.
        table.add_row(
            "LUKS key",
            Text(
                f"{state.key_state} -- re-flash with 'build-appliance-image --flash'",
                style="loom.danger",
            ),
        )

    if state.targets:
        for disk in state.targets:
            table.add_row(
                "Target",
                Text(devices.describe_disk(runner, disk).describe(), style="loom.warn"),
            )
        # Said out loud, because it is the one thing about the target list an
        # operator cannot read off it: these disks do not become alternatives to
        # choose between, they become a single volume.
        if len(state.targets) > 1:
            table.add_row(
                "",
                Text(
                    f"all {len(state.targets)} pooled into one"
                    f" {state.pool_bytes // constants.GIGABYTE} GB volume",
                    style="loom.quiet",
                ),
            )
    else:
        table.add_row("Target", "no eligible internal NVMe found")

    if state.verdict is not AutoInstall.ARMED:
        table.add_row(
            "Automatic", Text(f"no -- {reason(state.verdict)}", style="loom.quiet")
        )

    ui.show(table)
    ui.blank()


def show_menu(ui: Ui) -> None:
    table = Table.grid(padding=(0, 1))
    table.add_column(width=4, justify="right", style="loom.quiet")
    table.add_column()
    table.add_column(style="loom.quiet")
    for choice, entry in ENTRIES.items():
        table.add_row(
            f"{choice})",
            Text(entry.label, style=entry.style or ""),
            "[default]" if choice is DEFAULT_CHOICE else "",
        )
    ui.show(table)
    ui.blank()


def rescue_shell(ui: Ui) -> None:
    """A shell, with enough environment to be usable.

    `--norc --noprofile` so that nothing downstream resets PS1; the prompt is then
    set here and actually survives. PATH has to be spelled out for the same reason:
    the inherited one is what the wrapper built for the installer (cryptsetup,
    nvme-cli, gptfdisk, parted, nixos-install-tools), which is most of what a rescue
    shell wants but has neither the installer's own programs nor the rest of the
    system profile.

    TERM matters too: without it bash gives no line editing and nothing can clear the
    screen, which is most of what makes a bare shell feel broken.
    """
    ui.show(
        Text("  Rescue shell.", style="loom.head").append(
            " Type 'exit' or press Ctrl-D to return to the menu."
        )
    )
    ui.blank()

    environment = dict(os.environ)
    environment.update(
        {
            "HOME": environment.get("HOME", "/root"),
            "TERM": environment.get("TERM", "linux"),
            "PS1": r"[loom-installer:\w]\$ ",
            "PATH": ":".join(
                [
                    settings().bin_dir,
                    environment.get("PATH", ""),
                    "/run/current-system/sw/bin",
                ]
            ),
        }
    )
    subprocess.run(
        ["bash", "--norc", "--noprofile", "-i"], check=False, env=environment
    )


def halt_console(ui: Ui, subcommand: str, message: str) -> None:
    """`systemctl reboot` and `systemctl poweroff` only queue the job and return.

    Without the block afterwards the loop redraws the menu on top of the shutdown
    messages and offers a prompt that nobody should be answering.
    """
    ui.log(message)
    subprocess.run(["systemctl", subcommand], check=False)
    while True:
        time.sleep(3600)


def countdown_to_reboot(ui: Ui) -> None:
    """Reboot into the installed appliance, after a grace the operator can cut short.

    The grace exists for the recovery passphrase printed directly above: it is also
    on the installed box's login banner (box.nix), so this is convenience rather than
    the last chance to read it -- which is exactly why it is allowed to expire on its
    own instead of stranding the box at a prompt nobody returns to. The one case
    where the console does hold indefinitely is `hold_for_boot_order` below.

    Ctrl-C is the exception, and the opposite of the enter directly beside it: one
    brings the reboot forward, the other is somebody asking for more time with what
    is on the screen. So it holds, exactly as the degraded case does.
    """
    outcome = ui.countdown(
        "Press enter to reboot now; rebooting", REBOOT_GRACE_S, any_key=False
    )
    if outcome is Keypress.CANCELLED:
        ui.wait_for_enter("  Press enter to reboot. ")
    halt_console(ui, "reboot", "Rebooting.")


def hold_for_boot_order(ui: Ui) -> None:
    """The install succeeded, but the box will not boot into it without help.

    Restated here rather than left to the warnings `loom-install` already printed: those
    are emitted before the completion block and the recovery passphrase, so on a short
    console they are several screens up by the time anyone reads this.
    """
    ui.blank()
    ui.warn("The internal disk is NOT the default boot entry -- see the warning above.")
    ui.warn(
        "Put it first in the firmware boot order, or this box keeps booting the installer."
    )
    ui.blank()
    ui.wait_for_enter("  Press enter to reboot. ")
    halt_console(ui, "reboot", "Rebooting.")


def auto_countdown(ui: Ui) -> bool:
    """The grace period before an unattended install starts.

    True means go ahead. Any key cancels, not just enter: a stray keypress landing in
    the menu is harmless, whereas one that failed to register is a destroyed disk. EOF
    cancels too -- it means nobody can stop this, which is the last circumstance under
    which to go ahead and partition a disk. So does Ctrl-C, which arrives as a signal
    rather than as a byte (`Keypress.CANCELLED`) and is a keypress like any other here.
    """
    ui.blank()
    ui.show(
        Text(
            "  Installing automatically. Press any key to stop and use the menu.",
            style="loom.head",
        )
    )
    outcome = ui.countdown("Starting", settings().auto_grace, any_key=True)
    return outcome is Keypress.TIMEOUT


def run_install(ui: Ui, extra: list[str]) -> None:
    """Run the installer and deal with however it came back.

    A separate process rather than a call into `install.py`: the exit status is the
    contract between the two -- see `constants.EXIT_BOOT_ORDER_DEGRADED` -- and a
    menu that survives an installer crashing is a menu that can still offer a rescue
    shell.

    A finished install reboots rather than returning to the menu: the box is done,
    and every option left here either destroys the disk that was just written or does
    nothing for it. How long it waits first is the only thing the exit status
    decides.
    """
    status = _run_child(ui, [os.path.join(settings().bin_dir, "loom-install"), *extra])

    if status == 0:
        countdown_to_reboot(ui)
    elif status == constants.EXIT_BOOT_ORDER_DEGRADED:
        hold_for_boot_order(ui)
    else:
        if status == constants.EXIT_CANCELLED:
            # Said differently from a failure on purpose: the installer has already
            # printed what it did or did not do to the disks, and the operator asked
            # for this.
            ui.warn("Installation cancelled.")
        else:
            ui.warn("Installation failed.")
        ui.wait_for_enter("  Press enter to return to the menu. ")


def run_wipe(ui: Ui) -> None:
    status = _run_child(ui, [os.path.join(settings().bin_dir, "loom-wipe")])
    if status == constants.EXIT_CANCELLED:
        ui.warn("Wipe cancelled.")
    elif status != 0:
        ui.warn("Wipe failed.")
    ui.wait_for_enter("  Press enter to return to the menu. ")


def _run_child(ui: Ui, argv: list[str]) -> int:
    """Hand the console to `loom-install` or `loom-wipe`, and take it back.

    Ctrl-C at a console goes to every process in the foreground group, so the menu
    gets one at the same instant the child does -- and `subprocess.run` answers that
    by killing the child: it waits a quarter of a second and sends SIGKILL. A child
    killed there has no chance to unmount /mnt, close the LUKS mapping or say what it
    left behind, which is precisely what an interrupted install has to do.

    So the menu goes deaf for the duration and the child owns the keypress. Safe here
    and nowhere else: this process is doing nothing but waiting, and the one thing
    that could go wrong -- no way left to interrupt the menu itself -- is not a thing
    the menu wants, since it is `Restart=always` on tty1 and exiting buys nobody
    anything.

    SIG_IGN is inherited across exec, so `loom-install` and `loom-wipe` arm their own
    handler first thing in `main`. Without that pair this makes them uninterruptible
    rather than interruptible-and-tidy.

    `console_restored` is the other half, and it is not about Ctrl-C at all: a child
    that dies without unwinding -- by SIGKILL, by OOM -- leaves the terminal however
    it had it, and a menu redrawn onto a console with echo off is a box that looks
    broken.
    """
    with console_restored(ui), ignoring_interrupts():
        return subprocess.run(argv, check=False).returncode


def loop(ui: Ui, runner: CommandRunner) -> None:
    """Round and round until the box reboots, powers off, or is installed.

    The one catch site for an operator saying no to the menu itself. Every prompt in
    here raises `Aborted` on Ctrl-C, and the answer to all of them is the same: draw the
    menu again. Exiting would be worse than useless -- systemd restarts this service two
    seconds later (installer.nix), and all that would have happened is that the screen
    was cleared.
    """
    while True:
        try:
            _one_pass(ui, runner)
        except (Aborted, KeyboardInterrupt):
            continue


def _one_pass(ui: Ui, runner: CommandRunner) -> None:
    """Draw the menu once, and do whatever was chosen."""
    state = inspect(runner)
    show_status(ui, runner, state)
    show_menu(ui)

    if state.verdict is AutoInstall.ARMED:
        if auto_countdown(ui):
            # Marked before the run, not after. This service is Restart=always
            # (installer.nix), so a menu that dies part way through an install has to
            # come back to a prompt -- not to a second countdown onto a disk the
            # first attempt already began partitioning. A reboot clears it, which is
            # how a retry works.
            _mark_attempted()
            run_install(ui, ["--auto"])
        else:
            # Stopping the countdown has to stick for the same reason, and for one
            # more: without this, cancelling, taking the rescue shell and leaving it
            # lands back here with the countdown running again -- and the second one
            # may well expire with nobody still at the keyboard.
            _mark_declined()
        return

    answer = ui.prompt(f"  Choice [{DEFAULT_CHOICE}]: ") or DEFAULT_CHOICE
    match answer:
        case Choice.INSTALL:
            run_install(ui, [])
        case Choice.WIPE:
            run_wipe(ui)
        case Choice.REBOOT:
            halt_console(ui, "reboot", "Rebooting.")
        case Choice.POWEROFF:
            halt_console(ui, "poweroff", "Powering off.")
        case Choice.RESCUE:
            rescue_shell(ui)
        case _:
            ui.warn(f"Not a choice: {answer}")


def _mark_attempted() -> None:
    with open(constants.AUTO_MARKER, "w", encoding="utf-8"):
        pass


def _mark_declined() -> None:
    with open(constants.AUTO_DECLINED, "w", encoding="utf-8"):
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loom-menu", description="The Loom appliance installer's console menu."
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])

    ui = build_ui()
    sys.excepthook = crash_handler(ui, constants.CRASH_LOG)

    try:
        loop(ui, Subprocess())
    except SettingsError as error:
        ui.warn(str(error))
        return 1
    except KeyboardInterrupt:
        # A backstop, and meant to be unreachable: `loop` catches this itself, because
        # a menu that exits on Ctrl-C only comes back two seconds later with the
        # screen cleared.
        return constants.EXIT_CANCELLED
    return 0


if __name__ == "__main__":
    sys.exit(main())
