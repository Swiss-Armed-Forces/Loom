"""The two boot entries, and what differs between them.

Run mode and first-time setup are one closure and one specialisation (modes.nix), so
most of what separates them is invisible until something is read out of the other
system's store path -- which is what these do rather than booting the specialisation.
"""

import re
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def boot_modes(appliance: "Machine", subtest: "Subtest", params: Params) -> str:
    with subtest("both boot modes exist and differ in the right way"):
        # The first-time-setup specialisation is what lets one box both fetch
        # images online and then run entirely offline. Its *name* is also the
        # boot menu entry -- NixOS builds the title from distroName plus this
        # attribute -- so a rename here silently renames what the operator is
        # told to pick in Documentation/appliance.md.
        specialisations = appliance.succeed(
            "ls /run/current-system/specialisation/"
        ).split()
        assert "first-time-setup" in specialisations, specialisations

        # Run mode serves the network and starts Loom offline.
        #
        # The flags are not in the unit file: `script = ...` compiles to
        # ExecStart=<store path of a generated script>, so grepping the output
        # of `systemctl cat` for them matches nothing at all. Follow the
        # indirection and read the script the unit actually runs.
        unit = appliance.succeed("systemctl cat loom.service")
        match = re.search(r"ExecStart=(\S+)", unit)
        assert match, unit
        start_script = appliance.succeed(f"cat {match.group(1)}")
        assert "--offline" in start_script, start_script
        # And deliberately *not* --expose. Publishing the stack is
        # loom-expose's job now (see exposure below), and the two cannot be
        # combined: DNAT happens in nat PREROUTING, ahead of the routing
        # decision that would hand a packet to a tunnel's local socket.
        assert "--expose" not in start_script, start_script
        # First-time setup fetches instead, and must not serve DHCP.
        setup_sys = appliance.succeed(
            "readlink -f /run/current-system/specialisation/first-time-setup"
        ).strip()
        appliance.succeed(f"test -e {setup_sys}/etc/systemd/system/loom-fetch.service")
        appliance.fail(f"test -e {setup_sys}/etc/systemd/system/dnsmasq.service")

        _setup_mode_powers_off(appliance, setup_sys)
        _platform_flags(appliance, setup_sys, start_script, params)
        _kernel_command_lines(appliance, setup_sys)

    return setup_sys


def _platform_flags(
    appliance: "Machine", setup_sys: str, start_script: str, params: Params
) -> None:
    """The flags modes.nix derives from the platform reach *both* modes."""
    # --scaling is the one where the two modes are not merely consistent but
    # coupled. It is the only thing that installs KEDA, so a first-time setup
    # that ran without it leaves no KEDA images in minikube's store -- and run
    # mode, air-gapped by then, has no way to fetch what the fetch skipped. The
    # symptom would be a box that comes up with its ScaledObjects referring to a
    # controller that is not there, which nothing else here would catch.
    fetch_script = _fetch_script(appliance, setup_sys)
    for mode, script in [("run", start_script), ("setup", fetch_script)]:
        assert ("--scaling" in script) == params.autoscaling, f"{mode}: {script}"
        # And the pairing up.sh rejects outright. Asserted from the same two
        # scripts rather than from the platform, so this still holds if some
        # future flag starts contributing --no-resources of its own.
        if "--scaling" in script:
            assert "--no-resources" not in script, f"{mode}: {script}"


def _fetch_script(appliance: "Machine", setup_sys: str) -> str:
    """The script loom-fetch runs, through the same indirection as loom.service's."""
    fetch_unit = appliance.succeed(
        f"cat {setup_sys}/etc/systemd/system/loom-fetch.service"
    )
    match = re.search(r"ExecStart=(\S+)", fetch_unit)
    assert match, fetch_unit
    return appliance.succeed(f"cat {match.group(1)}")


def _setup_mode_powers_off(appliance: "Machine", setup_sys: str) -> None:
    """First-time setup ends by powering the box off."""
    # And it ends by powering the box off rather than leaving it up for
    # somebody to reboot: the default entry serves DHCP and *.loom on the
    # appliance NIC, which must not happen on whatever network the images
    # were just fetched over. Same ExecStart indirection as above -- the
    # specialisation's units cannot be read with `systemctl cat`.
    fetch_unit = appliance.succeed(
        f"cat {setup_sys}/etc/systemd/system/loom-fetch.service"
    )
    # Both modes share modes.nix's `commonService`, so the state directories
    # checked on loom.service in state_directories reach this unit by the same
    # definition. Asserted here anyway, cheaply, because the consequence is
    # worse in this mode: a fetch that warms the wrong minikube store leaves the
    # box with hours of downloads that run mode cannot find.
    assert "MINIKUBE_HOME=" in fetch_unit, fetch_unit
    fetch_script = _fetch_script(appliance, setup_sys)
    assert "poweroff" in fetch_script, fetch_script


def _kernel_command_lines(appliance: "Machine", setup_sys: str) -> None:
    """What each mode puts on the screen, which lives only on the command line."""
    # The two modes also differ in what they put on the screen, and that
    # difference lives only on the kernel command line. Run mode hides the
    # log behind the splash; first-time setup, which takes hours, keeps it.
    run_cmdline = appliance.succeed("cat /run/current-system/kernel-params")
    for param in ["quiet", "splash"]:
        assert param in run_cmdline.split(), run_cmdline
    setup_cmdline = appliance.succeed(f"cat {setup_sys}/kernel-params")
    assert "plymouth.enable=0" in setup_cmdline.split(), setup_cmdline

    # Neither mode may name a *numbered* VT as a console. `console=ttyN`
    # does not just redirect output there, it makes that VT the foreground
    # one -- which once left this box showing the kernel log while the
    # banner and the press-a-key prompt sat on a tty1 nobody could see or
    # type into. `console=tty0` is exempt and is what the test framework
    # itself passes: tty0 means "whichever VT is current", so it moves
    # nothing. A specialisation only *adds* to its parent's command line,
    # so checking both is checking every combination.
    for cmdline in [run_cmdline, setup_cmdline]:
        vt_consoles = [
            p for p in cmdline.split() if re.fullmatch(r"console=tty[1-9][0-9]*", p)
        ]
        assert not vt_consoles, cmdline


def mode_sessions(appliance: "Machine", subtest: "Subtest", setup_sys: str) -> None:
    with subtest("both modes run the same session, following their own unit"):
        # Same indirection as above: /etc/profile names the session script,
        # which names the pane-1 script, which names the unit. Reading the
        # chain is the only way to see the difference between the two modes
        # without booting the specialisation.
        def progress_script(profile):
            console = re.search(
                r"/nix/store/\S+-loom-console/bin/loom-console",
                appliance.succeed(f"cat {profile}"),
            )
            assert console, profile
            progress = re.search(
                r"/nix/store/\S+-loom-progress/bin/loom-progress",
                appliance.succeed(f"cat {console.group(0)}"),
            )
            assert progress, console.group(0)
            return appliance.succeed(f"cat {progress.group(0)}")

        run_pane = progress_script("/etc/profile")
        assert "loom.service" in run_pane, run_pane
        assert "loom-fetch.service" not in run_pane, run_pane
        setup_pane = progress_script(f"{setup_sys}/etc/profile")
        assert "loom-fetch.service" in setup_pane, setup_pane
