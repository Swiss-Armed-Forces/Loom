# The wired-NIC fallback: what happens on a box no platform matches.
#
# tests/appliance.nix asserts the opposite -- that a VM whose only NIC is virtio
# comes up with no `loom0` at all -- and switches this off to do so. That is the
# behaviour every supported platform gets, because their `netMatch` hits. This
# test covers the box nobody wrote a platform for, which is the case that used to
# need a new USB stick to recover from.
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

  # The driver's own mypy cannot resolve scripts/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  node.specialArgs = specialArgs;

  # The three nodes take `common` through `imports` rather than `common // { ...
  # }`, because `//` is a shallow merge: `dual` sets `virtualisation.vlans` and
  # that replaced the whole `virtualisation` attribute, silently dropping the
  # memory and disk sizes above. The module system merges the levels below the
  # first, which is what was meant.
  nodes = {
    # One NIC: the unambiguous case, and the one that motivated all of this.
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

    # The fallback switched off: the old behaviour, still reachable.
    disabled = {
      imports = [ common ];
      loom.autoSelectInterface = pkgs.lib.mkForce false;
    };
  };

  # The test itself is scripts/appliance_interface_fallback.py, so that the
  # repository's Python hooks reach it -- see scripts/driver.py for why, and for why
  # `skipTypeCheck` is set above.
  testScript = ''
    ${builtins.readFile ./scripts/appliance_interface_fallback.py}

    run(single, dual, disabled, start_all=start_all, subtest=subtest)
  '';
}
