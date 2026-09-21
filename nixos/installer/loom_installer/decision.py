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


class AutoInstall(StrEnum):
    """The verdict, or the reason there is not one."""

    ARMED = "armed"
    ATTEMPTED = "attempted"
    NO_BOOT_MEDIUM = "no-boot-medium"
    NO_KEY = "no-key"
    NO_TARGET = "no-target"
    TOO_SMALL = "too-small"
    ALREADY_INSTALLED = "already-installed"


@dataclass(frozen=True)
class AutoInstallInputs:
    """Everything the rule below is allowed to look at."""

    # The per-boot marker. After one attempt the disks may be half-written, and
    # probing them says nothing useful.
    attempted: bool
    # The medium we booted from, or None when it could not be identified.
    boot_disk: str | None
    key_state: KeyState
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
    AutoInstall.NO_BOOT_MEDIUM: "the boot medium is ambiguous",
    AutoInstall.NO_KEY: "the stick carries no LUKS key",
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
        Refusal(inputs.attempted, AutoInstall.ATTEMPTED),
        Refusal(inputs.boot_disk is None, AutoInstall.NO_BOOT_MEDIUM),
        Refusal(inputs.key_state is not KeyState.PRESENT, AutoInstall.NO_KEY),
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
