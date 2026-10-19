# Boots a --wifi appliance in a VM and asserts the access point actually comes up.
#
# Separate from tests/appliance.nix rather than a second node in it, because that
# test deliberately forces dnsmasq off and clears `networking.interfaces` -- the
# two things this one exists to exercise. It also keeps the default build's
# "radios are disabled" subtest honest: that assertion means nothing if the same
# file can be read as covering a build where they are not.
#
# The radio is mac80211_hwsim, the kernel's virtual 802.11 device. It implements
# enough of a real card for hostapd to bring a genuine BSS up, so this checks the
# hostapd configuration and the bridge wiring rather than only asserting that the
# generated files look right.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomSubnet,
}:
let
  ssid = "loom-test01";
  psk = "abcde-fghij-klmno-pqrst";
  boxAddress = "${loomSubnet}.1";

  # The DHCP client the lease subtest runs, on the box itself. Shared with
  # tests/appliance-dhcp.nix, which reads the same server's lease off the wire
  # instead of off the bridge; see that file for why it is guest code and not
  # part of the loom_tests package.
  dhcp-probe = import ./dhcp-probe.nix { inherit pkgs; };
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-wifi";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;

    loom.wifi = {
      enable = true;
      inherit ssid psk;
    };

    # The DHCP client the lease subtest runs, on the box itself. Added to this
    # node only -- it has no business in an image that gets flashed.
    environment.systemPackages = [ dhcp-probe ];

    # One virtual radio. Without `radios=1` the module creates two, and the
    # `Type = "wlan"` match in platforms/*.nix would rename whichever udev saw
    # first while the other kept its kernel name -- making the test's outcome
    # depend on probe order.
    boot.kernelModules = [ "mac80211_hwsim" ];
    boot.extraModprobeConfig = "options mac80211_hwsim radios=1";

    # Deliberately NOT clearing `networking.interfaces` the way
    # tests/appliance.nix does. That force exists there because the appliance
    # address sits on loom0, which never materialises in a VM -- the platform's
    # wired match is by driver and this NIC is virtio -- so the address unit
    # would wait forever on a .device that never appears.
    #
    # With --wifi the address sits on the bridge instead, and the bridge is
    # created unconditionally. So this node is a wifi-only box with no wired port
    # at all, which is exactly the case `networking.bridges.<n>.interfaces = [ ]`
    # exists for: it must still come up, still get its address, and still serve
    # DHCP and DNS with nothing plugged in.

    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
  };

  # The test itself is loom_tests/wifi.py, so that the repository's Python
  # hooks reach it -- see loom_tests/driver.py for why, and for why `skipTypeCheck` is
  # set above.
  testScript = ''
    from loom_tests.wifi import Params, run

    run(
        appliance,
        start_all=start_all,
        subtest=subtest,
        params=Params(
            ssid="${ssid}",
            psk="${psk}",
            box_address="${boxAddress}",
        ),
    )
  '';
}
