"""The USB key guard, which powers the box off when its key leaves.

Everything here manipulates the guard's devices, and the last subtest really does let
the machine power itself off -- which is the only way to know that half works. So these
run last, and nothing may be added after `powers_off`.

`deadline` spends a poweroff of its own, on the guard's arm deadline rather than on a
removal, so it runs against the second machine tests/appliance.nix boots for it.

There is no USB stick and no LUKS root in a VM, so the key and the root are loop devices
the test builds and points the guard at through symlinks. That is also what the box sees
after a re-insert: a stick can come back on a different node.
"""

import re
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def idle(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("the guard stays idle when there is no key"):
        # This is the recovery boot: somebody unlocked the disk by typing the
        # passphrase, so there is no stick at all. Powering such a box off
        # would make it unrepairable, since the console is the only way in.
        appliance.wait_for_unit("loom-key-guard.service")
        # `grep`, not `grep -q`, in every pipeline below. The driver wraps each
        # command in `set -eo pipefail`, and -q makes grep exit on the first
        # matching line -- so the producer on the left gets EPIPE on whatever it
        # writes next, and the pipeline fails *because* the match was found.
        # `loom-key-guard status` prints three more lines after the one being
        # matched, which makes that a coin toss on every run. Without -q grep
        # reads its input to the end and nothing is ever killed mid-write.
        appliance.wait_until_succeeds(
            "loom-key-guard status | grep 'loom-key-guard: idle' >/dev/null"
        )
        appliance.succeed(
            "journalctl --unit loom-key-guard.service | grep 'the guard stays idle' >/dev/null"
        )
        # Said once, not every interval for the life of the box.
        idle_lines = appliance.succeed(
            "journalctl --unit loom-key-guard.service | grep -c 'the guard stays idle'"
        )
        assert idle_lines.strip() == "1", idle_lines


def deadline(box: "Machine", subtest: "Subtest") -> None:
    with subtest("a box that booted from a stick and cannot arm powers off"):
        # On its own machine: this ends in a poweroff, and the appliance node
        # spends its own on the removal path at the end of this file.
        box.wait_for_unit("loom-key-guard.service")

        # The witness stage 1 writes on a box whose key partition was present
        # when the root was unlocked (box-hardware.nix). There is no LUKS root
        # in a VM, so the deadline is inert until this exists -- which is what
        # keeps it away from every other node in the suite.
        witness = "/run/loom/key-guard/booted-with-key"
        box.succeed(f"test ! -e {witness}")

        # Nobody has pressed a key on this machine, so tty1 is still at the
        # banner and a state change has to redraw it. Rewriting the issue file
        # is not enough: agetty paints it once and then blocks (box.nix), so
        # the getty being restarted is what proves the screen followed.
        getty = "autovt@tty1.service"
        painted = box.succeed(
            f"systemctl show --property=MainPID --value {getty}"
        ).strip()

        box.succeed(f"mkdir -p $(dirname {witness}) && touch {witness}")
        box.succeed("systemctl restart loom-key-guard.service")

        box.wait_until_succeeds(
            f'test "$(systemctl show --property=MainPID --value {getty})" '
            f'!= "{painted}"'
        )

        box.wait_until_succeeds(
            "loom-key-guard status | grep 'arm deadline' >/dev/null"
        )
        box.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep 'powers off in' >/dev/null"
        )
        # The banner says so too, on the screen an operator who never logs in
        # is looking at.
        box.succeed(
            "grep -q 'powers off 60 seconds after boot' /run/issue.d/50-loom.issue"
        )

        box.wait_for_shutdown()


def recovery_boot_stays_up(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("a box booted on the recovery passphrase is left up"):
        # The same clock the machine above dies on, on a box with no witness.
        # Nothing to wait for but the absence of an event, so this asserts the
        # guard's own reasoning rather than sitting out a deadline: no witness,
        # no deadline, and `status` never grows the line the other box grew.
        appliance.succeed("test ! -e /run/loom/key-guard/booted-with-key")
        appliance.succeed("test ! -e /run/loom/key-guard/deadline")
        appliance.fail("loom-key-guard status | grep 'arm deadline' >/dev/null")


def arms(appliance: "Machine", subtest: "Subtest", params: Params) -> str:
    with subtest("the guard arms on a key that opens the root"):
        appliance.succeed(f"mkdir -p {params.key_guard.directory}")
        appliance.succeed(
            "dd if=/dev/urandom of=/var/keyguard-key.img bs=4096 count=1 status=none"
        )
        # 32M: a LUKS2 header is 16M, and the container needs no payload here.
        appliance.succeed("truncate --size=32M /var/keyguard-root.img")
        root_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-root.img"
        ).strip()
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()

        # The same parameters install.sh formats with, pbkdf2 included -- argon2
        # would want more memory than this VM has.
        appliance.succeed(
            "cryptsetup luksFormat --type luks2 --batch-mode --pbkdf pbkdf2 "
            f"--pbkdf-force-iterations 1000 --key-file {key_loop} "
            f"--keyfile-size 4096 {root_loop}"
        )
        appliance.succeed(f"ln -sf {root_loop} {params.key_guard.root_device}")
        appliance.succeed(f"ln -sf {key_loop} {params.key_guard.key_device}")

        appliance.wait_until_succeeds(
            "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
        )
        # The banner follows the guard rather than reporting what was true at
        # boot, because it is the only thing an operator who never logs in sees.
        appliance.wait_until_succeeds(
            "grep -q 'USB key guard: armed' /run/issue.d/50-loom.issue"
        )
        assert "\\" not in appliance.succeed("cat /run/issue.d/50-loom.issue")

    return key_loop


def cancels(
    appliance: "Machine", subtest: "Subtest", params: Params, key_loop: str
) -> str:
    with subtest("a key that is put back in time cancels the shutdown"):
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep 'USB KEY REMOVED' >/dev/null"
        )

        # Back well inside the grace window, and deliberately on whatever loop
        # device is free now rather than the old one: a re-inserted stick can
        # come back on a different node, and the bytes are the identity.
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()
        appliance.succeed(f"ln -sf {key_loop} {params.key_guard.key_device}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep 'Shutdown cancelled' >/dev/null"
        )
        appliance.succeed(
            "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
        )

    return key_loop


def foreign_key(
    appliance: "Machine", subtest: "Subtest", params: Params, key_loop: str
) -> str:
    with subtest("a foreign key does not keep the box alive"):
        # A stick carrying a partition named loom-key is not the stick this
        # disk was encrypted with. Presence alone cannot tell the two apart;
        # the fingerprint taken at arm time can.
        appliance.succeed(
            "dd if=/dev/urandom of=/var/keyguard-other.img bs=4096 count=1 status=none"
        )
        other_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-other.img"
        ).strip()
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.succeed(f"ln -sf {other_loop} {params.key_guard.key_device}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep 'USB KEY REMOVED' >/dev/null"
        )

        # Put the real one back so the next subtest starts from a known state.
        appliance.succeed(f"losetup --detach {other_loop}")
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()
        appliance.succeed(f"ln -sf {key_loop} {params.key_guard.key_device}")
        appliance.wait_until_succeeds(
            "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
        )

    return key_loop


def action_per_mode(appliance: "Machine", subtest: "Subtest", setup_sys: str) -> None:
    with subtest("both boot modes power off, on the same deadline"):
        # Asserted from the two generated scripts rather than by booting the
        # specialisation: the stick is what the box is entitled to run from,
        # and neither mode may be merely advisory. Only a `--debug` image warns
        # instead, which tests/appliance-debug.nix covers. Same ExecStart
        # indirection as loom.service above -- the values are baked into the
        # script, not visible in the unit.
        def guard_constant(system_path, name):
            unit = appliance.succeed(
                f"cat {system_path}/etc/systemd/system/loom-key-guard.service"
            )
            exec_start = re.search(r"ExecStart=(\S+)", unit)
            assert exec_start, unit
            script = appliance.succeed(f"cat {exec_start.group(1)}")
            # Tolerates the quotes lib.escapeShellArg adds only when it has to.
            value = re.search(rf"^readonly {name}='?(\w+)'?$", script, re.M)
            assert value, script
            return value.group(1)

        for system in ("/run/current-system", setup_sys):
            assert guard_constant(system, "ACTION") == "poweroff"
            assert guard_constant(system, "ARM_DEADLINE") == "180"


def powers_off(appliance: "Machine", subtest: "Subtest", key_loop: str) -> None:
    with subtest("pulling the key powers the box off"):
        # The end of the test, literally: this shuts the machine down. Nothing
        # may be added below, and nothing short of watching it happen proves
        # that the box a stick was pulled from actually stops.
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.wait_for_shutdown()
