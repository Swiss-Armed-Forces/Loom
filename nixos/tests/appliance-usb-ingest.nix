# USB auto-ingest: what gets mounted, what never does, and how.
#
# tests/appliance.nix deliberately does not cover this. It asserts the values
# box.nix restates from up.sh; this one boots a box with extra disks, puts real
# filesystems on them, and checks the decisions usb-ingest.nix makes about them.
#
# The transfer itself is not exercised here -- that needs a running cluster, and
# the crawler's half is unit-tested in backend/crawler/tests. What is exercised
# is everything that happens before a byte moves, which is where the mistakes
# that matter live: mounting the wrong device, or mounting the right one wrongly.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomSubnet,
}:
let
  # Where the test pretends the key guard keeps its state, so the guard's verdict
  # can be set by hand. The real guard needs a LUKS volume and a stick; what this
  # module consumes from it is two small files.
  guardDir = "/run/loom-usbtest-keyguard";
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-usb-ingest";

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;
    # What this test writes goes to the scratch disks below; the node's own root
    # only carries what is ingested off them, which is a handful of small files
    # -- 28 MB, measured. See tests/appliance.nix for why the number is a cap
    # rather than a cost.
    virtualisation.diskSize = 2048;

    # Four scratch disks: vdb..vde. They are virtio rather than USB, which is why
    # every check below drives the command directly instead of going through the
    # udev rule -- the rule's ID_BUS=="usb" match cannot fire on virtio, and
    # faking it would be testing the fake.
    virtualisation.emptyDiskImages = [
      256
      256
      256
      256
    ];

    # The test framework drives networking itself.
    services.dnsmasq.enable = pkgs.lib.mkForce false;
    networking.interfaces = pkgs.lib.mkForce { };

    environment.systemPackages = with pkgs; [
      dosfstools
      e2fsprogs
      exfatprogs
      ntfs3g
      util-linux
      jq
    ];
  };

  testScript = ''
    import re

    appliance.wait_for_unit("multi-user.target")

    INGEST = "loom-usb-ingest --key-guard-state-dir ${guardDir}"


    def set_guard(state, device=None):
        appliance.succeed("mkdir -p ${guardDir}")
        appliance.succeed(f"echo {state} > ${guardDir}/state")
        if device:
            appliance.succeed(f"echo {device} > ${guardDir}/device")
        else:
            appliance.succeed("rm -f ${guardDir}/device")


    def plan(device):
        return appliance.succeed(f"{INGEST} --dry-run {device} 2>&1")


    with subtest("the armed key disk is never ingested"):
        # The central guarantee of this module. Pulling this stick powers the box
        # off ten seconds later (key-guard.nix), so touching it is not an option.
        appliance.succeed("mkfs.vfat /dev/vdb")
        set_guard("armed", "/dev/vdb")

        output = plan("/dev/vdb")

        assert "Not ingesting" in output, output
        assert "key guard" in output, output

    with subtest("an ordinary stick beside the key disk is still ingested"):
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        set_guard("armed", "/dev/vdb")

        output = plan("/dev/vdc")

        assert "Not ingesting" not in output, output
        assert "/dev/vdc" in output, output

    with subtest("Loom's own media is excluded even with the guard idle"):
        # A box booted on the recovery passphrase never arms the guard, and then
        # partition labels are the only thing standing between the installer
        # stick -- 60 GB of container images -- and the index.
        appliance.succeed(
            "sgdisk --zap-all /dev/vdd "
            "&& sgdisk --new=1:0:0 --change-name=1:loom-live-store /dev/vdd "
            "&& udevadm settle"
        )
        appliance.succeed("mkfs.ext4 -F /dev/vdd1")
        set_guard("idle")

        output = plan("/dev/vdd")

        assert "Not ingesting" in output, output
        assert "loom-live-store" in output, output

    with subtest("a refused container format is skipped with a reason"):
        appliance.succeed("mkfs.ext4 -F /dev/vde")
        appliance.succeed(
            "cryptsetup luksFormat --batch-mode --pbkdf pbkdf2 "
            "--pbkdf-force-iterations 1000 /dev/vde <<<'passphrase' || true"
        )
        appliance.succeed("udevadm settle")
        set_guard("armed", "/dev/vdb")

        output = plan("/dev/vde")

        assert "refused" in output, output
        assert "LUKS" in output, output

    with subtest("known filesystems get their own driver and options"):
        set_guard("armed", "/dev/vdb")
        appliance.succeed("mkfs.ntfs --fast /dev/vdc")

        output = plan("/dev/vdc")

        # FUSE rather than the in-kernel ntfs3, deliberately: this box parses
        # filesystems handed to it by strangers.
        assert "ntfs-3g" in output, output

    with subtest("journalled filesystems are mounted without replaying"):
        # `-o ro` alone still writes to a dirty ext4. This is the assertion that
        # the media is not modified by being read.
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        set_guard("armed", "/dev/vdb")

        output = plan("/dev/vdc")

        assert "noload" in output, output
        assert "ro," in output, output

    with subtest("the computed mount options are ones the kernel accepts"):
        # A wrong mount option is not ignored -- it fails the mount outright. So
        # take the options the planner produced and actually mount with them.
        appliance.succeed("mkfs.ext4 -F /dev/vdc")
        options = appliance.succeed(
            f"{INGEST} --dry-run /dev/vdc | sed -n 's/.*opts=//p' | head -1"
        ).strip()
        assert "noload" in options, options

        appliance.succeed("mkdir -p /mnt/probe")
        appliance.succeed(f"mount -o {options} -t ext4 /dev/vdc /mnt/probe")
        appliance.succeed("mountpoint /mnt/probe")
        appliance.succeed("umount /mnt/probe")

    with subtest("a read-only block device still mounts"):
        # blockdev --setro is applied before every mount, so the options above
        # have to work against a device the kernel refuses to write.
        appliance.succeed("blockdev --setro /dev/vdc")
        appliance.succeed(f"mount -o {options} -t ext4 /dev/vdc /mnt/probe")
        appliance.succeed("umount /mnt/probe")
        appliance.succeed("blockdev --setrw /dev/vdc")

    with subtest("the service and the udev rule are wired up"):
        appliance.succeed("systemctl cat 'loom-usb-ingest@.service' >&2")
        rules = appliance.succeed("cat /etc/udev/rules.d/*.rules")
        assert 'ENV{ID_BUS}=="usb"' in rules, "udev rule is missing its USB match"
        assert "loom-usb-ingest@" in rules, "udev rule does not start the service"

    with subtest("every binary the service shells out to is on its own PATH"):
        # Same reasoning as tests/appliance.nix's check for loom.service: a unit's
        # PATH is not systemPackages, and the two drifting is what once shipped a
        # box whose loom.service died on `awk: command not found`. Here the PATH
        # lives in the wrapper makeWrapper generated, so that is what gets asked.
        wrapper = appliance.succeed("readlink -f $(which loom-usb-ingest)").strip()
        # Parsed in Python rather than with sed: the quoting a shell one-liner
        # would need cannot be written inside a Nix indented string.
        wrapper_text = appliance.succeed(f"cat {wrapper}")
        # One `PATH='<store path>'$PATH` line per entry -- makeWrapper prepends
        # them one at a time rather than writing a single colon-joined
        # assignment, so reading only the first match would ask about the
        # package's own bin and nothing else.
        entries = re.findall(r"PATH='(/nix/store[^']*)'\$PATH", wrapper_text)
        assert entries, f"no PATH entries found in the wrapper {wrapper}"
        wrapped_path = ":".join(dict.fromkeys(entries))

        for binary in ["mc", "kubectl", "lsblk", "mount", "blockdev", "ntfs-3g", "tmux"]:
            # The shell is named by store path, not as `sh`: the point of the
            # check is that PATH holds nothing but what the wrapper puts there,
            # and `env` resolves the command it is given on that same PATH.
            appliance.succeed(
                f"env --ignore-environment PATH={wrapped_path} "
                f"${pkgs.runtimeShell} -c 'command -v {binary}'"
            )

    with subtest("status reports cleanly before anything has been ingested"):
        appliance.succeed("loom-usb-status")
  '';
}
