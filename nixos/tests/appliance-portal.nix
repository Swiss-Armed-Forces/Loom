# The captive portal page, booted, with no cluster behind it.
#
# The `--require-client-cert` build, which nothing else in this directory boots:
# tests/appliance.nix asserts the opposite of it (no loopback proxies, plain http
# served) and tests/appliance-units.nix reads its unit edges off an evaluation
# without starting anything. Without this test the one image where a visitor
# cannot get in without a certificate is never booted at all, and an nginx that
# cannot start is nothing's failure.
#
# Division of labour with the two tests next to it, which must not be collapsed
# into this one:
#
#   appliance-units.nix                 the decisions, on every platform, in seconds
#   loom_tests/appliance/portal.py      the rendered nginx configuration, as text
#   this                                what a request actually gets back
#
# The last is not a restatement of the first two. Which server block answers a
# probe is nginx's decision, taken from two `server_name` values and a
# `default_server` flag together, and it is the decision that keeps a phone
# offering "Sign in to network" instead of quietly falling back to mobile data.
#
# The node has the appliance's own network, the way tests/appliance-dhcp.nix does
# and for the same reason: the page is bound to the portal address, which only
# exists because `loom-interface-fallback` renames this node's one NIC to loom0
# and network.nix puts two addresses on it. A node that forced that off would be
# testing a listener nothing could reach.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomSubnet,
}:
let
  portalAddress = "${loomSubnet}.2";
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-portal";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check
  # that runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;

    # The build under test. Everything the page offers beyond "Open Loom" and the
    # trust anchor hangs off this one option.
    loom.mtls.enable = true;

    virtualisation.memorySize = 1024;
    virtualisation.diskSize = 2048;

    # Drop qemu's default user-mode NIC, as tests/appliance-dhcp.nix does: the
    # framework numbers vlan interfaces from eth1 and qemu-vm.nix adds eth0
    # underneath them, so a node that asks for one vlan boots with two wired
    # ports -- and the interface fallback would have a choice to make where this
    # test needs it to have none.
    virtualisation.qemu.networkingOptions = pkgs.lib.mkForce [ ];

    # Loom cannot come up in a test VM -- no images, no cluster -- and that is the
    # state under test rather than a limitation of it: `loom-portal-certificate`
    # waits for a secret that never arrives, so the page serves its "Loom is still
    # starting" answers, which is what every visitor gets for the first hours of a
    # real box's life too.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
  };

  testScript = ''
    from loom_tests.portal_page import Params, run

    run(
        appliance,
        start_all=start_all,
        subtest=subtest,
        params=Params(
            portal_address="${portalAddress}",
            portal_host="portal.loom",
            frontend_host="frontend.loom",
        ),
    )
  '';
}
