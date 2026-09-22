"""The box no platform matches: which wired NIC becomes loom0, and what is said.

Three nodes, because the answer differs by what the box has: one wired port, two, and
the fallback switched off -- which is the old behaviour, still reachable.

Nothing here is interpolated from the .nix
file:
every value this asserts is a name
the appliance itself chooses.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest


def _single_nic_claimed(single: "Machine", subtest: "Subtest") -> None:
    with subtest("a single wired NIC is claimed as loom0"):
        single.wait_for_unit("loom-interface-fallback.service")
        single.succeed("test -e /sys/class/net/loom0")

        record = single.succeed("cat /run/loom/interface-fallback")
        assert "LOOM_FALLBACK_REASON=auto" in record, record
        # Nothing is left carrying the kernel-assigned name it arrived with.
        assert "LOOM_FALLBACK_INTERFACE=loom0" not in record, record


def _claimed_nic_is_real(single: "Machine", subtest: "Subtest") -> None:
    with subtest("the claimed NIC is a real one, not a bridge or a radio"):
        # The selection excludes anything with a DEVTYPE, which is how a WWAN modem
        # -- ARPHRD_ETHER, real device, no wireless directory -- stays out.
        devtype = single.succeed(
            "cat /sys/class/net/loom0/uevent | grep -c '^DEVTYPE=' || true"
        ).strip()
        assert devtype == "0", f"loom0 has a DEVTYPE: {devtype}"
        single.succeed("test -e /sys/class/net/loom0/device")


def _console_says_so(single: "Machine", subtest: "Subtest") -> None:
    with subtest("the console says the NIC was claimed automatically"):
        single.wait_for_unit("loom-network-check.service")
        issue = single.succeed("cat /run/issue.d/60-loom-network.issue")
        assert "claimed automatically" in issue, issue
        # No backslashes: agetty eats them out of an issue file as escapes.
        assert "\\" not in issue, issue


def _rerunning_changes_nothing(single: "Machine", subtest: "Subtest") -> None:
    with subtest("re-running the fallback changes nothing"):
        before = single.succeed("cat /run/loom/interface-fallback")
        single.succeed("systemctl restart loom-interface-fallback.service")
        single.succeed("test -e /sys/class/net/loom0")
        assert single.succeed("cat /run/loom/interface-fallback") == before


def _one_of_two_claimed(dual: "Machine", subtest: "Subtest") -> None:
    with subtest(
        "with two wired NICs exactly one is claimed, and the other is offered"
    ):
        dual.wait_for_unit("loom-interface-fallback.service")
        dual.succeed("test -e /sys/class/net/loom0")

        record = dual.succeed("cat /run/loom/interface-fallback")
        assert "LOOM_FALLBACK_REASON=auto" in record, record

        alternatives = _alternatives(record)
        assert len(alternatives) == 1, record

        # The alternative is named on the console, because "move the cable" is the
        # whole recovery path for a box that came up on the wrong port.
        dual.wait_for_unit("loom-network-check.service")
        issue = dual.succeed("cat /run/issue.d/60-loom-network.issue")
        assert alternatives[0] in issue, issue
        assert "move the cable" in issue, issue


def _lowest_device_path_wins(dual: "Machine", subtest: "Subtest") -> None:
    with subtest(
        "the choice is the lowest device path, not whatever udev finished first"
    ):
        chosen_path = dual.succeed(
            "basename $(readlink -f /sys/class/net/loom0/device)"
        ).strip()
        other = _alternatives(dual.succeed("cat /run/loom/interface-fallback"))[0]
        other_path = dual.succeed(
            f"basename $(readlink -f /sys/class/net/{other}/device)"
        ).strip()
        assert chosen_path < other_path, f"picked {chosen_path}, lower was {other_path}"


def _alternatives(record: str) -> list[str]:
    """The wired ports the fallback did not take."""
    return [
        line.split("=", 1)[1]
        for line in record.splitlines()
        if line.startswith("LOOM_FALLBACK_ALTERNATIVES=")
    ][0].split()


def _switched_off(disabled: "Machine", subtest: "Subtest") -> None:
    with subtest("switched off, nothing is claimed and the warning stands"):
        disabled.fail("test -e /sys/class/net/loom0")
        disabled.fail("systemctl cat loom-interface-fallback.service")

        disabled.wait_for_unit("loom-network-check.service")
        issue = disabled.succeed("cat /run/issue.d/60-loom-network.issue")
        assert "does not exist" in issue, issue
        assert "\\" not in issue, issue


def run(
    single: "Machine",
    dual: "Machine",
    disabled: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
) -> None:
    """The whole test, as the .nix file calls it."""
    start_all()

    for machine in (single, dual, disabled):
        machine.wait_for_unit("multi-user.target")

    _single_nic_claimed(single, subtest)
    _claimed_nic_is_real(single, subtest)
    _console_says_so(single, subtest)
    _rerunning_changes_nothing(single, subtest)

    _one_of_two_claimed(dual, subtest)
    _lowest_device_path_wins(dual, subtest)

    _switched_off(disabled, subtest)
