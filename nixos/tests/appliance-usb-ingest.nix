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

  # The driver's own mypy cannot resolve scripts/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

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

  # The test itself is scripts/appliance_usb_ingest.py, so that the repository's
  # Python hooks reach it -- see scripts/driver.py for why, and for why
  # `skipTypeCheck` is set above.
  testScript = ''
    ${builtins.readFile ./scripts/appliance_usb_ingest.py}

    run(
        appliance,
        subtest=subtest,
        params=Params(
            guard_dir="${guardDir}",
            shell="${pkgs.runtimeShell}",
        ),
    )
  '';
}
