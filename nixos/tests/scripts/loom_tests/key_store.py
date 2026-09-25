"""The key guard on a box whose stick key is passphrase-locked.

tests/appliance-key-store.nix says why this is a test of its own. In short: on a
`--lock-key` box the guard cannot prove the stick opens the root, so it arms on
`cryptsetup isLuks` and leans on the fingerprint for identity -- and if that branch
is wrong the guard sits idle forever and pulling the stick does nothing, silently.

The three things asserted here are the three the weaker check still has to deliver:
it arms on a real container, it notices the container leaving, and it refuses a
different container. The third is the one that would be lost if somebody
"simplified" the fingerprint away now that the oracle is gone.
"""

from typing import TYPE_CHECKING

from loom_tests.appliance.params import KeyGuardPaths

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest

__all__ = ["KeyGuardPaths", "run"]

# The passphrase over the container. Fixed rather than generated: what is under
# test is the guard, and generating one is cicd/build_appliance_image.sh's job.
PASSPHRASE = "correct-horse-battery-staple-stick-key-phrase"

# The parameters cicd/build_appliance_image.sh pins, restated so that a change
# there which the box could not afford fails here rather than in stage 1.
LUKS_FORMAT = (
    "cryptsetup luksFormat --type luks2 --batch-mode --pbkdf argon2id"
    " --pbkdf-force-iterations 4 --pbkdf-memory 1048576 --pbkdf-parallel 4"
)


def run(
    locked: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
    key_guard: KeyGuardPaths,
) -> None:
    """The whole test, as tests/appliance-key-store.nix calls it."""
    start_all()
    locked.wait_for_unit("multi-user.target")

    oracle_is_off(locked, subtest)
    key_loop = arms_on_a_container(locked, subtest, key_guard)
    key_loop = notices_removal(locked, subtest, key_guard, key_loop)
    a_foreign_container_is_not_this_stick(locked, subtest, key_guard, key_loop)


def oracle_is_off(locked: "Machine", subtest: "Subtest") -> None:
    with subtest("the locked build drops the unlock oracle"):
        # Read off the generated script rather than inferred from behaviour, the
        # same way loom_tests/appliance/guard.py reads ACTION: this is the one
        # constant that decides which of the two arming paths runs, and asserting
        # it directly is what makes the rest of this file mean what it says.
        script = locked.succeed(
            "cat $(readlink -f /run/current-system/sw/bin/loom-key-guard)"
        )
        assert "readonly KEY_ORACLE=false" in script, (
            "the locked build still arms through the root oracle, which it has no"
            " key for -- the guard would never arm"
        )


def arms_on_a_container(
    locked: "Machine", subtest: "Subtest", key_guard: KeyGuardPaths
) -> str:
    with subtest("the guard arms on a passphrase-locked key container"):
        locked.succeed(f"mkdir -p {key_guard.directory}")

        # The stick as `build-appliance-image --flash --lock-key` leaves it: 32M,
        # a LUKS2 container, the key inside it. 32M because a LUKS2 header puts
        # the payload at 16M, which is why nixos/installer.nix sizes the
        # partition the way it does.
        locked.succeed("truncate --size=32M /var/keystore.img")
        key_loop = locked.succeed("losetup --find --show /var/keystore.img").strip()
        locked.succeed(f"printf %s {PASSPHRASE} >/var/keystore-pass")
        locked.succeed(f"{LUKS_FORMAT} --key-file /var/keystore-pass {key_loop}")

        # A root device for the guard to name. It is never opened on this box --
        # that is the entire point of the locked branch -- so it only has to
        # exist and be the thing `rootDevice` points at.
        locked.succeed("truncate --size=32M /var/keystore-root.img")
        root_loop = locked.succeed(
            "losetup --find --show /var/keystore-root.img"
        ).strip()

        locked.succeed(f"ln -sf {root_loop} {key_guard.root_device}")
        locked.succeed(f"ln -sf {key_loop} {key_guard.key_device}")

        locked.wait_until_succeeds(
            "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
        )
        # The banner follows the guard, the same as on an unlocked box: it is the
        # only thing an operator who never logs in sees.
        locked.wait_until_succeeds(
            "grep -q 'USB key guard: armed' /run/issue.d/50-loom.issue"
        )
        assert "\\" not in locked.succeed("cat /run/issue.d/50-loom.issue")

    return key_loop


def notices_removal(
    locked: "Machine", subtest: "Subtest", key_guard: KeyGuardPaths, key_loop: str
) -> str:
    with subtest("pulling the locked stick still starts the countdown"):
        locked.succeed(f"losetup --detach {key_loop}")
        locked.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service"
            " | grep 'USB KEY REMOVED' >/dev/null"
        )

        # Back inside the grace window, on whatever node is free now: a
        # re-inserted stick can come back somewhere else, and the header bytes
        # are the identity. This is the property the fingerprint has to carry on
        # a container exactly as it did on raw key bytes.
        key_loop = locked.succeed("losetup --find --show /var/keystore.img").strip()
        locked.succeed(f"ln -sf {key_loop} {key_guard.key_device}")
        locked.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service"
            " | grep 'Shutdown cancelled' >/dev/null"
        )

    return key_loop


def a_foreign_container_is_not_this_stick(
    locked: "Machine", subtest: "Subtest", key_guard: KeyGuardPaths, key_loop: str
) -> None:
    with subtest("another container does not keep the box alive"):
        # The assertion this file exists for. With the root oracle gone, a
        # `cryptsetup isLuks` that arms on any container at all would accept any
        # Loom stick in the world -- and pass every other subtest here. What
        # tells them apart is the fingerprint: two containers have two headers.
        locked.succeed("truncate --size=32M /var/keystore-other.img")
        other_loop = locked.succeed(
            "losetup --find --show /var/keystore-other.img"
        ).strip()
        locked.succeed(f"{LUKS_FORMAT} --key-file /var/keystore-pass {other_loop}")

        # Counted rather than grepped for. The previous subtest already put a
        # 'USB KEY REMOVED' in this journal, so a plain grep would pass here
        # without the guard having noticed anything at all -- which is precisely
        # the bug this subtest is for.
        before = _removals(locked)
        locked.succeed(f"losetup --detach {key_loop}")
        locked.succeed(f"ln -sf {other_loop} {key_guard.key_device}")
        locked.wait_until_succeeds(f"test $({_REMOVALS}) -gt {before}")
        locked.succeed(f"losetup --detach {other_loop}")


# `|| true`: grep exits non-zero on no matches, and zero is a legitimate count.
_REMOVALS = (
    "journalctl --unit loom-key-guard.service | grep -c 'USB KEY REMOVED' || true"
)


def _removals(locked: "Machine") -> int:
    return int(locked.succeed(_REMOVALS).strip())
