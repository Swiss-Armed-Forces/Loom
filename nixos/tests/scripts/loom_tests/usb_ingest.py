"""USB auto-ingest: what gets mounted, what never does, and how.

scripts/appliance.py deliberately does not cover this. It asserts the values box.nix
restates from up.sh; this one boots a box with extra disks, puts real filesystems on
them, and checks the decisions usb-ingest.nix makes about them.

The transfer itself is not exercised here -- that needs a running cluster, and the
crawler's half is unit-tested in backend/crawler/tests. What is exercised is everything
that happens before a byte moves, which is where the mistakes that matter live: mounting
the wrong device, or mounting the right one wrongly.
"""

import re
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


class Params(NamedTuple):
    """What the .nix file knows and this file cannot."""

    # Where the test pretends the key guard keeps its state, so the guard's verdict
    # can be set by hand. The real guard needs a LUKS volume and a stick; what this
    # module consumes from it is two small files.
    guard_dir: str
    # Named by store path rather than as `sh`, for the PATH check at the bottom.
    shell: str


def _ingest(params: Params) -> str:
    return f"loom-usb-ingest --key-guard-state-dir {params.guard_dir}"


def _set_guard(
    appliance: "Machine", params: Params, state: str, device: str | None = None
) -> None:
    """Put a verdict in front of the ingest, without a stick or a LUKS volume."""
    appliance.succeed(f"mkdir -p {params.guard_dir}")
    appliance.succeed(f"echo {state} > {params.guard_dir}/state")
    if device:
        appliance.succeed(f"echo {device} > {params.guard_dir}/device")
    else:
        appliance.succeed(f"rm -f {params.guard_dir}/device")


def _plan(appliance: "Machine", params: Params, device: str) -> str:
    """What the ingest would do with a device, without doing any of it."""
    return appliance.succeed(f"{_ingest(params)} --dry-run {device} 2>&1")


def _key_disk_excluded(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the armed key disk is never ingested"):
        # The central guarantee of this module. Pulling this stick powers the box off
        # ten seconds later (key-guard.nix), so touching it is not an option.
        appliance.succeed("mkfs.vfat /dev/vdb")
        _set_guard(appliance, params, "armed", "/dev/vdb")

        output = _plan(appliance, params, "/dev/vdb")

        assert "Not ingesting" in output, output
        assert "key guard" in output, output


def _ordinary_stick_ingested(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("an ordinary stick beside the key disk is still ingested"):
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        _set_guard(appliance, params, "armed", "/dev/vdb")

        output = _plan(appliance, params, "/dev/vdc")

        assert "Not ingesting" not in output, output
        assert "/dev/vdc" in output, output


def _loom_media_excluded(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("Loom's own media is excluded even with the guard idle"):
        # A box booted on the recovery passphrase never arms the guard, and then
        # partition labels are the only thing standing between the installer stick
        # -- 60 GB of container images -- and the index.
        appliance.succeed(
            "sgdisk --zap-all /dev/vdd "
            "&& sgdisk --new=1:0:0 --change-name=1:loom-live-store /dev/vdd "
            "&& udevadm settle"
        )
        appliance.succeed("mkfs.ext4 -F /dev/vdd1")
        _set_guard(appliance, params, "idle")

        output = _plan(appliance, params, "/dev/vdd")

        assert "Not ingesting" in output, output
        assert "loom-live-store" in output, output


def _refused_container(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a refused container format is skipped with a reason"):
        appliance.succeed("mkfs.ext4 -F /dev/vde")
        appliance.succeed(
            "cryptsetup luksFormat --batch-mode --pbkdf pbkdf2 "
            "--pbkdf-force-iterations 1000 /dev/vde <<<'passphrase' || true"
        )
        appliance.succeed("udevadm settle")
        _set_guard(appliance, params, "armed", "/dev/vdb")

        output = _plan(appliance, params, "/dev/vde")

        assert "refused" in output, output
        assert "LUKS" in output, output


def _filesystem_drivers(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("known filesystems get their own driver and options"):
        _set_guard(appliance, params, "armed", "/dev/vdb")
        appliance.succeed("mkfs.ntfs --fast /dev/vdc")

        output = _plan(appliance, params, "/dev/vdc")

        # FUSE rather than the in-kernel ntfs3, deliberately: this box parses
        # filesystems handed to it by strangers.
        assert "ntfs-3g" in output, output


def _no_journal_replay(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("journalled filesystems are mounted without replaying"):
        # `-o ro` alone still writes to a dirty ext4. This is the assertion that the
        # media is not modified by being read.
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        _set_guard(appliance, params, "armed", "/dev/vdb")

        output = _plan(appliance, params, "/dev/vdc")

        assert "noload" in output, output
        assert "ro," in output, output


def _mount_options_accepted(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> str:
    with subtest("the computed mount options are ones the kernel accepts"):
        # A wrong mount option is not ignored -- it fails the mount outright. So take
        # the options the planner produced and actually mount with them.
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        options = appliance.succeed(
            f"{_ingest(params)} --dry-run /dev/vdc | sed -n 's/.*opts=//p' | head -1"
        ).strip()
        assert "noload" in options, options

        appliance.succeed("mkdir -p /mnt/probe")
        appliance.succeed(f"mount -o {options} -t ext4 /dev/vdc /mnt/probe")
        appliance.succeed("mountpoint /mnt/probe")
        appliance.succeed("umount /mnt/probe")

    return options


def _read_only_device(appliance: "Machine", subtest: "Subtest", options: str) -> None:
    with subtest("a read-only block device still mounts"):
        # blockdev --setro is applied before every mount, so the options above have
        # to work against a device the kernel refuses to write.
        appliance.succeed("blockdev --setro /dev/vdc")
        appliance.succeed(f"mount -o {options} -t ext4 /dev/vdc /mnt/probe")
        appliance.succeed("umount /mnt/probe")
        appliance.succeed("blockdev --setrw /dev/vdc")


def _unit_and_rule(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("the service and the udev rule are wired up"):
        appliance.succeed("systemctl cat 'loom-usb-ingest@.service' >&2")
        rules = appliance.succeed("cat /etc/udev/rules.d/*.rules")
        assert 'ENV{ID_BUS}=="usb"' in rules, "udev rule is missing its USB match"
        assert "loom-usb-ingest@" in rules, "udev rule does not start the service"

    with subtest("removing a device is a rule of its own"):
        # What ends the console pane. It cannot be the ingest unit's own
        # ExecStopPost: that is a oneshot, so systemd stops it when the copy
        # finishes -- with the stick still in the box and its "done" row unread.
        appliance.succeed("systemctl cat loom-usb-release.service >&2")
        rules = appliance.succeed("cat /etc/udev/rules.d/*.rules")
        assert 'ACTION=="remove"' in rules, "nothing reacts to a device going away"
        assert (
            "loom-usb-release.service" in rules
        ), "the remove rule does not start the sweep"


# A device that is still plugged in, as the ingest would have left it after a copy
# that finished. Written by hand because the transfer itself needs a cluster; what is
# under test here is what `--release` does with such a record, which is nothing.
_FINISHED_RECORD = (
    '{{"device": "{device}", "kernel_name": "{kernel}", "name": "stick-{kernel}",'
    ' "outcome": {{"stage": "done", "message": ""}},'
    ' "volume": {{"path": "{device}1", "index": 1, "count": 1}},'
    ' "counts": {{"total": 4096, "copied": 4096, "objects": 7, "failures": 0}},'
    ' "updated": 0.0}}'
)


def _pane_outlives_the_copy(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a finished device keeps its row until it is unplugged"):
        # The default progress directory, deliberately: the point is that the real
        # binary, with the real paths, leaves a finished record alone.
        directory = "/run/loom/usb-progress"
        appliance.succeed(f"mkdir -p {directory}")

        present = _FINISHED_RECORD.format(device="/dev/vdc", kernel="vdc")
        appliance.succeed(f"printf '%s' '{present}' > {directory}/vdc.json")
        # vdz is not a device on this machine, which is what a stick that has been
        # pulled looks like from here.
        gone = _FINISHED_RECORD.format(device="/dev/vdz", kernel="vdz")
        appliance.succeed(f"printf '%s' '{gone}' > {directory}/vdz.json")

        appliance.succeed(f"{_ingest(params)} --release /dev/vdc")

        # `succeed`/`fail` are the assertion: either raises with the machine's own
        # output when the box does not agree.
        appliance.succeed(f"test -e {directory}/vdc.json")
        appliance.fail(f"test -e {directory}/vdz.json")

        appliance.succeed(f"rm -f {directory}/vdc.json")


def _wrapper_path(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("every binary the service shells out to is on its own PATH"):
        # Same reasoning as scripts/appliance.py's check for loom.service: a unit's
        # PATH is not systemPackages, and the two drifting is what once shipped a box
        # whose loom.service died on `awk: command not found`. Here the PATH lives in
        # the wrapper makeWrapper generated, so that is what gets asked.
        wrapper = appliance.succeed("readlink -f $(which loom-usb-ingest)").strip()
        # Parsed in Python rather than with sed: the quoting a shell one-liner would
        # need cannot be written inside a Nix indented string.
        wrapper_text = appliance.succeed(f"cat {wrapper}")
        # One `PATH='<store path>'$PATH` line per entry -- makeWrapper prepends them
        # one at a time rather than writing a single colon-joined assignment, so
        # reading only the first match would ask about the package's own bin and
        # nothing else.
        entries = re.findall(r"PATH='(/nix/store[^']*)'\$PATH", wrapper_text)
        assert entries, f"no PATH entries found in the wrapper {wrapper}"
        wrapped_path = ":".join(dict.fromkeys(entries))

        for binary in [
            "mc",
            "kubectl",
            "lsblk",
            "mount",
            "blockdev",
            "ntfs-3g",
            "tmux",
        ]:
            # The shell is named by store path, not as `sh`: the point of the check
            # is that PATH holds nothing but what the wrapper puts there, and `env`
            # resolves the command it is given on that same PATH.
            appliance.succeed(
                f"env --ignore-environment PATH={wrapped_path} "
                f"{params.shell} -c 'command -v {binary}'"
            )


def _status_before_ingest(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("status reports cleanly before anything has been ingested"):
        appliance.succeed("loom-usb-status")


def _mc_runs_in_the_units_environment(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest(
        "mc starts with the environment the unit has, and says why it did not"
    ):
        # `env -u HOME` is the whole point: systemd sets $HOME only for units that set
        # `User=` (systemd.exec(5)) and the ingest units run as root without one, so
        # every run of this by hand had a home directory the service never has. Without
        # one, mc resolves its config directory by shelling out to `getent` -- which is
        # not on the wrapper's PATH -- and dies before it reads a single argument.
        #
        # The endpoint is a port nothing listens on and the kubeconfig does not exist,
        # so this fails without a cluster, and fails *after* the point where a broken
        # environment would have stopped it. `--cluster-wait` is what keeps it short:
        # the real default is an hour, because that is how long a box that has just
        # been switched on takes to bring Loom up.
        _set_guard(appliance, params, "armed", "/dev/vdb")
        output = appliance.fail(
            f"env -u HOME {_ingest(params)} --endpoint https://127.0.0.1:1 "
            "--kubeconfig /nonexistent --cluster-wait 5 /dev/vdc 2>&1"
        )

        assert "mcConfigDir" not in output, output
        assert "getent" not in output, output
        # That it reached the network is the assertion, not that it failed: our own
        # headline names the endpoint, so every way mc can die on its own command line
        # -- a config directory it cannot resolve, an environment variable it cannot
        # parse into the bool a flag wants -- would pass a test that only looked for
        # the address.
        assert "connection refused" in output, output
        assert "could not parse" not in output, output
        # And that it got there by *waiting*, which is what a stick plugged into a box
        # still starting Loom has to do. Registering the endpoint used to probe it,
        # so an endpoint that was not up yet failed the ingest outright and this wait
        # was unreachable in exactly the case it was written for.
        assert "never answered in 5 seconds" in output, output
        # And the failure it did have is on the operator's screen, not only in the
        # journal: a count of failures with no reason is not something anybody
        # standing at the box can act on.
        assert "was not ingested" in output, output

        record = appliance.succeed("cat /run/loom/usb-progress/vdc.json")
        assert '"stage": "failed"' in record, record
        assert '"message": ""' not in record, record

        appliance.succeed("rm -f /run/loom/usb-progress/vdc.json")


def run(appliance: "Machine", *, subtest: "Subtest", params: Params) -> None:
    """The whole test, as the .nix file calls it."""
    appliance.wait_for_unit("multi-user.target")

    _key_disk_excluded(appliance, subtest, params)
    _ordinary_stick_ingested(appliance, subtest, params)
    _loom_media_excluded(appliance, subtest, params)
    _refused_container(appliance, subtest, params)
    _filesystem_drivers(appliance, subtest, params)
    _no_journal_replay(appliance, subtest, params)
    # The options the planner produced are mounted with twice: once on an ordinary
    # device, once on one the kernel refuses to write.
    options = _mount_options_accepted(appliance, subtest, params)
    _read_only_device(appliance, subtest, options)
    _unit_and_rule(appliance, subtest)
    _pane_outlives_the_copy(appliance, subtest, params)
    _wrapper_path(appliance, subtest, params)
    _status_before_ingest(appliance, subtest)
    # Last, because it is the only subtest that runs an ingest for real rather than
    # planning one: it leaves a progress record behind, and cleans it up itself.
    _mc_runs_in_the_units_environment(appliance, subtest, params)
