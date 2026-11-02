# The wired-NIC fallback: what happens on a box no platform matches.
#
# tests/appliance.nix asserts the opposite -- that a VM whose only NIC is virtio
# comes up with no `loom0` at all -- and switches this off to do so. That is the
# behaviour every supported platform gets, because their `netMatch` hits. This
# test covers the box nobody wrote a platform for, which without the fallback
# would need a new USB stick to recover from.
#
# A virtio NIC is perfect here for the same reason it is awkward there: nothing
# in `platforms/` matches it, so the fallback is reached exactly as it would be
# on unknown hardware.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomSubnet,
}:
let
  common = {
    imports = applianceModules;
    virtualisation.memorySize = 1024;
    # Three nodes run from this, and none of them writes anything: measured
    # usage is ~20 MB each. See tests/appliance.nix for why the number is a cap
    # rather than a cost.
    virtualisation.diskSize = 2048;
    # The test framework drives networking itself; the appliance's DHCP server
    # would fight it.
    services.dnsmasq.enable = pkgs.lib.mkForce false;
    networking.interfaces = pkgs.lib.mkForce { };
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
    # Drop qemu's default user-mode NIC. The framework numbers the vlan
    # interfaces from eth1 (nixpkgs nixos/lib/testing/network.nix) and
    # qemu-vm.nix adds eth0 underneath them, so a node that asks for one vlan
    # boots with *two* wired ports -- indistinguishable from each other to the
    # fallback, which is right, and fatal to a test whose whole subject is how
    # many there are. Nothing here needs it: the driver talks to these machines
    # over the backdoor, not the network.
    virtualisation.qemu.networkingOptions = pkgs.lib.mkForce [ ];
  };
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-interface-fallback";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check
  # that runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  # The three nodes take `common` through `imports` rather than `common // { ...
  # }`, because `//` is a shallow merge: `dual` sets `virtualisation.vlans`, which
  # would replace the whole `virtualisation` attribute and silently drop the
  # memory and disk sizes above. The module system merges the levels below the
  # first.
  nodes = {
    # One NIC: the unambiguous case.
    single = common;

    # Two NICs, so the choice has to be made rather than fallen into. An extra
    # vlan gives the node a second interface.
    dual = {
      imports = [ common ];
      virtualisation.vlans = [
        1
        2
      ];
    };

    # The fallback switched off: nothing is claimed and no loom0 exists at all.
    disabled = {
      imports = [ common ];
      loom.autoSelectInterface = pkgs.lib.mkForce false;
    };

    # A platform that declines the driver behind the only wired port there is.
    # The fallback is on, runs, and must come up with nothing rather than claim
    # a port the platform said not to -- which on the Spark is a QSFP cage that
    # sorts ahead of the RJ45 and carries nothing without a transceiver.
    #
    # `mkForce` because platforms/<id>.nix may define this already; the Spark
    # does. Without it `appliance-test interface-fallback --platform spark`
    # would be a definition conflict rather than a test.
    excluded = {
      imports = [ common ];
      loom.platform.netExcludeDrivers = pkgs.lib.mkForce [ "virtio_net" ];
    };
  };

  # The test itself is loom_tests/interface_fallback.py, so that the repository's
  # Python hooks reach it -- see loom_tests/driver.py for why, and for why
  # `skipTypeCheck` is set above.
  testScript = ''
    from loom_tests.interface_fallback import Nodes, run

    run(
        Nodes(
            single=single,
            dual=dual,
            disabled=disabled,
            excluded=excluded,
        ),
        start_all=start_all,
        subtest=subtest,
    )
  '';
}
