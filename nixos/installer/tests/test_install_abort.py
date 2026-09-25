"""What an install does when it stops before it is finished.

Two moments, and they are opposites. Before the action word is typed nothing has been
written, so a Ctrl-C has to leave the box exactly as it was found -- if any of these
tests ever sees an sgdisk, an operator who said no has lost a disk. After it, the disks
are already being written to and there is no undoing that: what matters instead is that
the box is let go of, so the menu's next option can still reach it, and that the screen
says what the box now is.

Everything below goes through `install.run` rather than its steps, because the ordering
between the interlock, the keystore and the destructive window *is* the behaviour. The
disks are a `FakeRunner`: nothing here runs a command, so a mistake in this file cannot
cost anything, and a mistake in install.py shows up as a command that was issued.
"""

import pytest
from fakes import (
    FakeRunner,
    printed,
    scripted_ui,
    with_installable_box,
)

from loom_installer import constants, install
from loom_installer.console import Aborted

DISK = "/dev/nvme0n1"
ZAP = ["sgdisk", "--zap-all", DISK]
DEACTIVATE = ["vgchange", "--activate", "n", "loom"]
UNMOUNT = ["umount", "--recursive", constants.MOUNT]


def test_ctrl_c_at_the_interlock_touches_no_disk() -> None:
    # The one that matters. An operator who changes their mind while looking at the
    # list of disks about to be destroyed must be able to get out of it, and Ctrl-C
    # is what they will reach for before they think to type anything else.
    runner = with_installable_box(FakeRunner())
    ui = scripted_ui(interrupted=True)

    with pytest.raises(Aborted):
        install.run(runner, ui, auto=False)

    written = [call for call in runner.calls if call[0] in ("sgdisk", "wipefs")]
    assert written == []


def test_a_refused_interlock_is_not_told_the_box_is_broken() -> None:
    # The teardown and its warning belong to the window after the interlock. Reaching
    # them from a refusal would tell somebody who stopped in time that their box no
    # longer boots.
    runner = with_installable_box(FakeRunner())
    ui = scripted_ui(interrupted=True)

    with pytest.raises(Aborted):
        install.run(runner, ui, auto=False)

    assert "NOT boot" not in printed(ui)


def test_an_interrupt_after_the_disks_are_written_lets_go_of_them() -> None:
    # The menu is still running and its next option may be a wipe. A mounted /mnt, an
    # open dm-crypt mapping or an active volume group all keep the partition tables
    # busy, and nothing else on this box will release them.
    runner = with_installable_box(FakeRunner())
    runner.interrupts(ZAP)

    with pytest.raises(KeyboardInterrupt):
        install.run(runner, scripted_ui(), auto=True)

    # Sliced at the interruption: `partition` releases storage on the way *in* as
    # well, so the same commands appear before it and asserting on the whole list
    # would pass with the teardown deleted.
    after = runner.calls[runner.calls.index(ZAP) + 1 :]
    assert UNMOUNT in after
    assert DEACTIVATE in after


def test_an_interrupt_after_the_disks_are_written_says_the_box_will_not_boot() -> None:
    # "Installation failed." on its own reads like nothing happened. This is the one
    # operation in the installer that is not atomic, and the operator has to be told
    # that the box in front of them is now half installed.
    runner = with_installable_box(FakeRunner())
    runner.interrupts(ZAP)
    ui = scripted_ui()

    with pytest.raises(KeyboardInterrupt):
        install.run(runner, ui, auto=True)

    assert "NOT boot" in printed(ui)


def test_a_failed_command_is_treated_as_the_same_kind_of_stop() -> None:
    # An sgdisk that dies leaves the box in exactly the state a Ctrl-C does. It used
    # to print one line and return to a menu that said "Installation failed", with
    # nothing to say the disks had already been rewritten.
    runner = with_installable_box(FakeRunner())
    runner.raises[" ".join(ZAP)] = RuntimeError
    ui = scripted_ui()

    with pytest.raises(RuntimeError):
        install.run(runner, ui, auto=True)

    assert "NOT boot" in printed(ui)
    assert DEACTIVATE in runner.calls[runner.calls.index(ZAP) + 1 :]
