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
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-wifi";

  # The driver's own mypy cannot resolve scripts/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;

    loom.wifi = {
      enable = true;
      inherit ssid psk;
    };

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

  # The test itself is scripts/appliance_wifi.py, so that the repository's Python
  # hooks reach it -- see scripts/driver.py for why, and for why `skipTypeCheck` is
  # set above.
  testScript = ''
    ${builtins.readFile ./scripts/appliance_wifi.py}

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
