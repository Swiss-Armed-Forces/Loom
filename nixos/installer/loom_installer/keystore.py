"""Getting at the stick's key, whichever kind of stick this is.

An ordinary stick holds the 4096 key bytes on its `loom-key` partition and there is
nothing to do. A stick flashed with `build-appliance-image --lock-key` holds a LUKS2
container there instead, with the same 4096 bytes inside it, and getting at them costs
the word passphrase the build printed.

The whole point of this module is that only *one* thing differs between the two: the
path that holds the bytes. `install.encrypt`, `install.enroll_recovery_passphrase` and
`storage.pool_claimed_by_key` all take that path as a parameter and are identical either
way -- which is why none of them appears here.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from loom_installer import constants, devices
from loom_installer.commands import CommandRunner
from loom_installer.console import Ui
from loom_installer.settings import settings


class KeystoreError(RuntimeError):
    """The key container is there, and it did not open."""


# How many times somebody may mistype before the installer gives up.
#
# Three rather than one because this is a passphrase read off a printout and typed
# blind on a console keyboard whose layout nobody chose, and rather than unbounded
# because an installer sitting at a prompt forever is indistinguishable from one that
# has hung.
PASSPHRASE_ATTEMPTS = 3


def mapping_path() -> str:
    """Where the unlocked container appears, when there is one."""
    return os.path.join("/dev/mapper", settings().key_store.mapping)


@contextmanager
def unlocked_key(runner: CommandRunner, ui: Ui) -> Generator[str, None, None]:
    """Yield a path holding the 4096 plaintext key bytes at offset 0.

    On an ordinary stick that is the key partition itself and this does nothing at
    all -- no prompt, no mapping, no teardown. On a locked stick it is an open
    dm-crypt mapping over the partition, closed again on the way out however the
    caller leaves.

    Enter this *before* anything destructive. A mistyped passphrase then costs
    nothing, where the same mistake discovered after `partition` would leave a box
    with no pool and no way to make one.
    """
    if not settings().key_store.locked:
        yield constants.KEY_DEVICE
        return

    if not devices.is_key_container(runner, constants.KEY_DEVICE):
        raise KeystoreError(
            f"This stick was built with --lock-key, but {constants.KEY_LABEL} holds no"
            " LUKS2 container. It was flashed by a build that did not write one;"
            " re-flash it with 'build-appliance-image --flash --lock-key'."
        )

    _open(runner, ui)
    try:
        yield mapping_path()
    finally:
        # Best effort on purpose. The install either finished or raised, and a
        # mapping that will not close must not be what the operator is told about.
        runner.run(["cryptsetup", "close", settings().key_store.mapping])


def _open(runner: CommandRunner, ui: Ui) -> None:
    """Ask for the passphrase until it opens the container, or give up."""
    ui.log("This stick's key is passphrase-locked")

    # A mapping left over from an install that was killed rather than returned
    # from -- the menu runs `loom-install` as a subprocess, and an operator who
    # holds the power button gets exactly this. `cryptsetup open` would then fail
    # with "device already exists" on all three attempts, and the message an
    # operator with the correct passphrase would read is "wrong passphrase".
    runner.run(["cryptsetup", "close", settings().key_store.mapping])

    for attempt in range(1, PASSPHRASE_ATTEMPTS + 1):
        passphrase = ui.prompt_secret("  Key stick passphrase: ")
        # A pipe rather than a file or an argument, the same way the recovery
        # passphrase leaves `enroll_recovery_passphrase`: it never becomes a path
        # in /proc and never lands in anything another process can read.
        opened = runner.run(
            [
                "cryptsetup",
                "open",
                "--type",
                "luks2",
                "--key-file",
                "-",
                constants.KEY_DEVICE,
                settings().key_store.mapping,
            ],
            stdin=passphrase,
        )
        if opened.ok:
            return
        if attempt < PASSPHRASE_ATTEMPTS:
            ui.warn(f"  Wrong passphrase. {PASSPHRASE_ATTEMPTS - attempt} left.")

    raise KeystoreError(
        f"The key container did not open in {PASSPHRASE_ATTEMPTS} attempts."
        " The passphrase was printed when this stick was flashed."
    )
