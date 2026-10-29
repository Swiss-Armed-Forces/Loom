# The build that actually gets flashed, serving DHCP on loom0.
#
# Every other test in this directory either forces dnsmasq off or runs it on the
# --wifi bridge. The default image does neither: the appliance address and the
# DHCP server sit on loom0, a *renamed physical port*, and that combination is
# the one nothing else covers. There is no `network-setup.service` under this pin
# to hold dnsmasq back until the address exists, so network.nix has to name the
# ordering explicitly -- on the --wifi bridge and on loom0 alike.
#
# The race is reproduced rather than simulated. `loom-interface-fallback` renames
# this node's only NIC at network-pre.target, so
# sys-subsystem-net-devices-loom0.device appears late and pulls
# network-addresses-loom0.service in late -- while dnsmasq, ordered on
# network.target alone, is free to start first. That is the box, not a fixture.
#
# Division of labour with tests/appliance-units.nix, which must not be collapsed
# into this one: that test pins the unit edges, cheaply and on every platform
# including the --wifi build no x86_64 runner can boot. This one proves the end
# state -- that a lease actually comes back. With bind-dynamic in place, undoing
# only the ordering would probably leave this test green, because dnsmasq would
# start and pick the interface up a moment later. Both are needed.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomSubnet,
}:
let
  boxAddress = "${loomSubnet}.1";
  portalAddress = "${loomSubnet}.2";
  poolStart = "${loomSubnet}.100";
  # The other end of the same range network.nix configures, so the offer can be
  # judged against the pool rather than against its /24.
  poolEnd = "${loomSubnet}.200";

  # The visitor node's own address, deliberately below the pool so it cannot
  # collide with a lease the appliance hands out during the test.
  visitorAddress = "${loomSubnet}.50";

  dhcp-probe = import ./dhcp-probe.nix { inherit pkgs; };
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-dhcp";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check
  # that runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 1024;
    # A cap rather than a cost: the root is a sparse qcow2 and this node writes
    # about what the interface-fallback nodes do, which is ~20 MB.
    virtualisation.diskSize = 2048;

    # Drop qemu's default user-mode NIC, as tests/appliance-interface-fallback.nix
    # does and for the same reason: the framework numbers the vlan interfaces
    # from eth1 (nixpkgs nixos/lib/testing/network.nix) and qemu-vm.nix adds eth0
    # underneath them, so a node that asks for one vlan boots with *two* wired
    # ports -- and the fallback would have a choice to make where this test needs
    # it to have none. It also takes qemu's own DHCP server off the segment, so
    # the only server answering here is the one under test.
    virtualisation.qemu.networkingOptions = pkgs.lib.mkForce [ ];

    # Loom cannot come up in a test VM -- no images, no cluster -- and the
    # console session's first pane would fill with that failure.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];

    # Deliberately NOT forcing `services.dnsmasq.enable` off, and deliberately
    # NOT clearing `networking.interfaces`. Those two forces are what every other
    # test in this directory uses to keep the appliance's network out of the
    # framework's way, and they are exactly the two things under test here.
    #
    # They could not be partially taken back anyway: a nested definition under a
    # forced parent is discarded rather than merged (see nixos/vm.nix), so a node
    # that cleared `networking.interfaces` and then added loom0 back would get
    # nothing.
    #
    # `loom.autoSelectInterface` is left ON, which is what renames this node's
    # eth1 to loom0 -- the appliance behaviour on a box no platform matches, and
    # what makes the .device unit appear late enough for the race to be the real
    # one.
    #
    # One residual, and it is not a failure: the framework also declares
    # `networking.interfaces.eth1`, and after the rename that .device never
    # appears, so network-addresses-eth1.service is simply never started. It is
    # `wantedBy` that .device and nothing else, so nothing waits on it and
    # multi-user.target is unaffected. The driver reaches this machine over the
    # backdoor rather than over the network, so the lost framework address costs
    # nothing either.

    # The DHCP client the lease subtest runs, on the box itself. This node only --
    # it has no business in an image anybody flashes.
    environment.systemPackages = [ dhcp-probe ];
  };

  # A visitor's laptop, on the appliance's own segment.
  #
  # This node talks to the appliance over the network it serves: every other
  # assertion in the suite runs `curl` on the appliance itself with a hand-written
  # `Host:` header, which proves nginx answers a crafted request and says nothing
  # about whether a real client ever sends one.
  #
  # Same vlan, so this is the appliance's wire rather than the framework's. The
  # framework's own address on eth1 is cleared and a static one out of the
  # appliance subnet put there instead -- static rather than DHCP because the
  # lease itself is asserted from the appliance side by `loom-dhcp-probe`, and a
  # second DHCP client here would only add a wait. The default route is the point:
  # it is what sends this node's off-subnet traffic at the box, which is the whole
  # of what the lease now tells a real client to do.
  nodes.visitor =
    { pkgs, ... }:
    {
      virtualisation.memorySize = 512;
      virtualisation.diskSize = 1024;

      networking.useDHCP = false;
      networking.interfaces.eth1.ipv4.addresses = pkgs.lib.mkForce [
        {
          address = "${visitorAddress}";
          prefixLength = 24;
        }
      ];
      networking.defaultGateway = {
        address = "${boxAddress}";
        interface = "eth1";
      };
      networking.nameservers = [ "${boxAddress}" ];
      networking.firewall.enable = false;

      # `host` and `ping` are in the default system path already; curl is not.
      environment.systemPackages = [ pkgs.curl ];
    };

  # The test itself is loom_tests/dhcp.py, so that the repository's Python hooks
  # reach it -- see loom_tests/driver.py for why, and for why `skipTypeCheck` is
  # set above.
  testScript = ''
    from loom_tests.dhcp import Params, run

    run(
        appliance,
        visitor,
        start_all=start_all,
        subtest=subtest,
        params=Params(
            interface="loom0",
            box_address="${boxAddress}",
            portal_address="${portalAddress}",
            pool_start="${poolStart}",
            pool_end="${poolEnd}",
        ),
    )
  '';
}
