"""Whether this boot may install without anybody confirming it, and if not, why.

Deliberately pure: every input is already-gathered state, passed in. The device work
happens in the caller, which makes the rule itself something a test can exercise
exhaustively -- and this is the rule that decides whether a disk gets destroyed
unattended. tests/test_decision.py is that truth table.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import NamedTuple

from loom_installer import constants
from loom_installer.devices import KeyState


class BootState(StrEnum):
    """What has already happened on this boot, which no disk can be asked about.

    One value rather than two flags because the two are mutually exclusive answers to
    the same question, and because which of them outranks the other is a rule worth
    writing down once -- `decide_boot_state` below -- rather than leaving to the order
    two markers happen to be read in.
    """

    FRESH = "fresh"
    # An install was started. The disks may be half written, and nothing read off
    # them means anything.
    ATTEMPTED = "attempted"
    # Somebody stopped the countdown. Nothing was written, but a person was standing
    # here and said no.
    DECLINED = "declined"


def decide_boot_state(attempted: bool, declined: bool) -> BootState:
    """Which of the two markers the menu may have written wins.

    `attempted` does, and it is not close: the two can both be there -- an operator who
    stops one countdown and then chooses Install by hand -- and of the two, only that
    one means the disks have been touched.
    """
    if attempted:
        return BootState.ATTEMPTED
    if declined:
        return BootState.DECLINED
    return BootState.FRESH


class AutoInstall(StrEnum):
    """The verdict, or the reason there is not one."""

    ARMED = "armed"
    ATTEMPTED = "attempted"
    DECLINED = "declined"
    NO_BOOT_MEDIUM = "no-boot-medium"
    NO_KEY = "no-key"
    KEY_LOCKED = "key-locked"
    NO_TARGET = "no-target"
    TOO_SMALL = "too-small"
    ALREADY_INSTALLED = "already-installed"


@dataclass(frozen=True)
class AutoInstallInputs:
    """Everything the rule below is allowed to look at."""

    # What the menu has already done this boot, from its markers in /run.
    boot_state: BootState
    # The medium we booted from, or None when it could not be identified.
    boot_disk: str | None
    key_state: KeyState
    # Whether the stick's key is behind a passphrase (`--lock-key`). Nobody can
    # type one into an unattended install, so it is a refusal rather than a prompt.
    key_locked: bool
    target_count: int
    pool_bytes: int
    # Whether this stick already installed this box.
    claimed: bool


# What to tell the operator when the verdict is not `ARMED`.
#
# Every one of these ends at the menu, which is the safe outcome -- so this is not
# an error report but an explanation of why the box is waiting for them.
REASONS: dict[AutoInstall, str] = {
    AutoInstall.ATTEMPTED: "an install was already attempted this boot",
    AutoInstall.DECLINED: "the automatic install was stopped this boot",
    AutoInstall.NO_BOOT_MEDIUM: "the boot medium is ambiguous",
    AutoInstall.NO_KEY: "the stick carries no LUKS key",
    AutoInstall.KEY_LOCKED: "the stick's key needs a passphrase",
    AutoInstall.NO_TARGET: "there is no eligible internal disk",
    AutoInstall.TOO_SMALL: "the disks are too small",
    AutoInstall.ALREADY_INSTALLED: "this stick already installed this box",
}


class Refusal(NamedTuple):
    """One reason an unattended install may not start, and whether it applies."""

    applies: bool
    verdict: AutoInstall


def _refusals(inputs: AutoInstallInputs) -> list[Refusal]:
    """Every reason not to, in the order they are asked.

    A list rather than a chain of returns because the order is the rule: the marker
    comes first and before anything looks at a disk, since after one attempt this
    boot the disks may be half-written and nothing read off them means anything.
    """
    return [
        Refusal(inputs.boot_state is BootState.ATTEMPTED, AutoInstall.ATTEMPTED),
        # Directly after it, and before anything looks at a disk, for the same
        # reason: both are answers about this boot that no state on a disk can
        # overrule.
        Refusal(inputs.boot_state is BootState.DECLINED, AutoInstall.DECLINED),
        Refusal(inputs.boot_disk is None, AutoInstall.NO_BOOT_MEDIUM),
        Refusal(inputs.key_state is not KeyState.PRESENT, AutoInstall.NO_KEY),
        # Before the two disk questions below, because it is not a disk question:
        # a locked key needs somebody at the keyboard, and once that is settled
        # the state of the disks cannot change the answer. It is also what keeps
        # `pool_claimed_by_key` -- which needs the plaintext key this refusal
        # says nobody has -- from being asked at all (menu.py `inspect`).
        Refusal(inputs.key_locked, AutoInstall.KEY_LOCKED),
        Refusal(inputs.target_count == 0, AutoInstall.NO_TARGET),
        Refusal(inputs.pool_bytes < constants.MIN_POOL_BYTES, AutoInstall.TOO_SMALL),
        Refusal(inputs.claimed, AutoInstall.ALREADY_INSTALLED),
    ]


def decide(inputs: AutoInstallInputs) -> AutoInstall:
    """The rule: the first refusal that applies, or `ARMED` if none does."""
    for refusal in _refusals(inputs):
        if refusal.applies:
            return refusal.verdict
    return AutoInstall.ARMED


def reason(verdict: AutoInstall) -> str:
    """Why the box is sitting at a menu instead of installing.

    The fallback is the verdict's own name, so a verdict added without a reason is still
    explained -- badly, which is what tests/test_decision.py refuses.
    """
    return REASONS.get(verdict, str(verdict))
