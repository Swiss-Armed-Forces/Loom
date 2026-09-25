"""The rule that decides whether a disk is destroyed with nobody watching.

Run in the installer's own derivation (nixos/installer.nix), so a mistake here fails the
image build in seconds rather than at a box -- the same argument the suites under
nixos/usb-ingest/ and nixos/console-mouse/ are run for.

Only `decide` and `reason` are covered, and deliberately so: the rule is pure by
construction, every input handed to it in a dataclass, precisely so that it can be
exercised exhaustively without a disk anywhere near it. What gathers those inputs is
covered by test_devices.py and by nixos/tests/appliance-install.nix.
"""

import pytest

from loom_installer import constants
from loom_installer.decision import (
    AutoInstall,
    AutoInstallInputs,
    BootState,
    decide,
    decide_boot_state,
    reason,
)
from loom_installer.devices import KeyState

# Either side of MIN_POOL_BYTES (250 GB). NOT_ENOUGH is picked so that two of it
# clear the minimum and one of it does not, which is what the pooled case turns on.
ENOUGH = 300 * constants.GIGABYTE
NOT_ENOUGH = 140 * constants.GIGABYTE


def inputs(**overrides: object) -> AutoInstallInputs:
    """A box that would install by itself, minus whatever the caller breaks."""
    defaults: dict[str, object] = {
        "boot_state": BootState.FRESH,
        "boot_disk": "/dev/sda",
        "key_state": KeyState.PRESENT,
        "key_locked": False,
        "target_count": 1,
        "pool_bytes": ENOUGH,
        "claimed": False,
    }
    defaults.update(overrides)
    return AutoInstallInputs(**defaults)  # type: ignore[arg-type]


def test_a_fresh_box_with_one_big_enough_disk_installs_by_itself() -> None:
    assert decide(inputs()) is AutoInstall.ARMED


def test_two_disks_too_small_alone_are_armed_once_pooled() -> None:
    # The whole point of measuring the pool rather than each member: this box has no
    # disk that would pass on its own.
    verdict = decide(inputs(target_count=2, pool_bytes=NOT_ENOUGH * 2))
    assert verdict is AutoInstall.ARMED


def test_a_second_attempt_in_the_same_boot_never_starts() -> None:
    # Set by the menu before it hands over, so a service restart cannot count down
    # again onto a disk the first attempt already began partitioning.
    assert decide(inputs(boot_state=BootState.ATTEMPTED)) is AutoInstall.ATTEMPTED


def test_the_marker_outranks_every_other_verdict() -> None:
    # Including one that would itself have refused: after an attempt the disks may be
    # half written, and nothing read off them means anything.
    verdict = decide(
        inputs(
            boot_state=BootState.ATTEMPTED,
            boot_disk=None,
            key_state=KeyState.MISSING,
            target_count=0,
            pool_bytes=0,
            claimed=True,
        )
    )
    assert verdict is AutoInstall.ATTEMPTED


def test_a_stopped_countdown_stays_stopped_for_the_rest_of_the_boot() -> None:
    # Somebody was standing here and said no. Without this the menu re-arms the
    # countdown the moment it is drawn again -- after a systemd restart, or after a
    # trip through the rescue shell -- and the second one may expire with nobody
    # still at the keyboard.
    assert decide(inputs(boot_state=BootState.DECLINED)) is AutoInstall.DECLINED


def test_an_attempt_outranks_a_refusal() -> None:
    # Both markers can be there at once: an operator who stops one countdown and then
    # chooses Install by hand. Only one of them means the disks may be half written,
    # and that is the one that has to survive into the verdict.
    assert decide_boot_state(attempted=True, declined=True) is BootState.ATTEMPTED
    assert decide_boot_state(attempted=False, declined=True) is BootState.DECLINED
    assert decide_boot_state(attempted=False, declined=False) is BootState.FRESH


def test_an_ambiguous_boot_medium_refuses() -> None:
    # Two Loom sticks attached: `boot_disk` declines to guess, and guessing here is
    # how the wrong device gets erased.
    assert decide(inputs(boot_disk=None)) is AutoInstall.NO_BOOT_MEDIUM


@pytest.mark.parametrize("state", [KeyState.EMPTY, KeyState.MISSING])
def test_a_stick_with_no_key_refuses(state: KeyState) -> None:
    # Installing from one produces a box that encrypts itself and then never boots
    # again.
    assert decide(inputs(key_state=state)) is AutoInstall.NO_KEY


def test_a_passphrase_locked_key_refuses() -> None:
    # --lock-key: the key needs a passphrase, and an unattended install is by
    # definition the case where nobody is there to type one.
    assert decide(inputs(key_locked=True)) is AutoInstall.KEY_LOCKED


def test_a_locked_key_refuses_before_anything_reads_a_disk() -> None:
    # Ordering, not taste. `pool_claimed_by_key` -- the probe behind
    # ALREADY_INSTALLED -- opens the root with the key bytes this verdict says are
    # unreachable, so a box where both apply has to come out KEY_LOCKED. menu.py
    # leans on that to skip the probe entirely.
    verdict = decide(inputs(key_locked=True, claimed=True, target_count=0))
    assert verdict is AutoInstall.KEY_LOCKED


def test_no_eligible_disk_refuses() -> None:
    assert decide(inputs(target_count=0, pool_bytes=0)) is AutoInstall.NO_TARGET


def test_a_pool_under_the_minimum_refuses() -> None:
    assert decide(inputs(pool_bytes=NOT_ENOUGH)) is AutoInstall.TOO_SMALL


def test_a_box_this_stick_already_installed_is_left_alone() -> None:
    # The accident this guard exists for: cleared NVRAM or a firmware that re-scans
    # removable media boots the stick again, and the box reinstalls over its own
    # indexed data with nobody at the keyboard.
    assert decide(inputs(claimed=True)) is AutoInstall.ALREADY_INSTALLED


def test_a_box_installed_from_a_different_stick_is_still_armed() -> None:
    # A re-flashed stick carries a fresh key, so it cannot open that container and
    # re-provisioning stays unattended. This is the half of the guard that would be
    # easy to lose by making it test for a Loom layout instead.
    assert decide(inputs(claimed=False)) is AutoInstall.ARMED


def test_every_verdict_has_something_to_say_for_itself() -> None:
    # The reason line is the only explanation an operator gets for a box that is
    # sitting at a menu instead of installing, so none of them may come out blank --
    # and a new verdict added without a reason must fail here.
    for verdict in AutoInstall:
        if verdict is AutoInstall.ARMED:
            continue
        assert reason(verdict)
        assert reason(verdict) != str(verdict)
