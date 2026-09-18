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

  testScript = ''
    start_all()
    appliance.wait_for_unit("multi-user.target")

    with subtest("the radio is renamed and hostapd owns it"):
        appliance.wait_for_unit("hostapd.service")
        appliance.succeed("test -e /sys/class/net/loomwl0")

        # The SSID that reaches the air is the one that was built in, not a
        # default left behind by the module.
        conf = appliance.succeed("cat /run/hostapd/loomwl0.hostapd.conf")
        assert "ssid=${ssid}" in conf, conf
        # Transition mode: both key managements present, so a WPA2-only phone
        # and a WPA3 one can both associate. A regression to plain SAE here
        # would lock out the older half of the visitors this feature is for.
        assert "SAE" in conf and "WPA-PSK" in conf, conf
        assert "bridge=loombr0" in conf, conf

    with subtest("the bridge exists and carries the appliance address"):
        appliance.succeed("test -d /sys/class/net/loombr0/bridge")
        # hostapd enslaves its own interface; nothing in the Nix config does.
        appliance.succeed("test -e /sys/class/net/loombr0/brif/loomwl0")

        # The whole point of the bridge: the address, the DHCP server and the
        # resolver sit on it rather than on the wired NIC, so a client reaching
        # the box over the air is on the same network as one that plugged in.
        addrs = appliance.succeed("ip -4 addr show loombr0")
        assert "${boxAddress}/24" in addrs, addrs
        appliance.wait_for_unit("dnsmasq.service")
        # Resolved through the box's own resolver, at the bridge address, which
        # is what a joining client will use -- not through /etc/hosts.
        #
        # -t A on purpose. A bare `host` also asks for AAAA and MX, and dnsmasq
        # refuses both: `address=/loom/<ipv4>` synthesises A records only and
        # there is no upstream to forward the rest to. That is how the appliance
        # has always answered; it makes `host` exit non-zero on a lookup that
        # actually succeeded.
        answer = appliance.succeed("host -t A frontend.loom ${boxAddress}")
        assert "has address ${boxAddress}" in answer, answer

    with subtest("bridge ports forward immediately"):
        # With STP off the kernel puts ports straight into forwarding, so the
        # default 15-second forward delay should never apply. Pinned and checked
        # because the failure mode is invisible from the box: a phone's first
        # DHCPDISCOVER is swallowed and it self-assigns a 169.254 address, which
        # looks like a broken access point rather than like a bridge timer.
        assert appliance.succeed("cat /sys/class/net/loombr0/bridge/stp_state").strip() == "0"
        assert appliance.succeed("cat /sys/class/net/loombr0/bridge/forward_delay").strip() == "0"

    with subtest("wifi is unblocked but bluetooth is still gone"):
        # --wifi opts a box into an access point, not into every radio it owns.
        for module in ["bluetooth", "btusb"]:
            appliance.succeed(f"grep -R 'blacklist {module}' /etc/modprobe.d/")
        for module in ["cfg80211", "mac80211"]:
            appliance.fail(f"grep -R 'blacklist {module}' /etc/modprobe.d/")
        appliance.wait_for_unit("loom-rfkill-block.service")
        rfkill = appliance.succeed("rfkill list")
        assert "Wireless LAN" in rfkill, rfkill
        assert "yes" not in rfkill.split("Wireless LAN")[1].split("\n\n")[0], rfkill

    with subtest("the login screen carries the credentials and a scannable QR"):
        appliance.wait_for_unit("loom-issue.service")
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        # The credentials are never dropped, whatever the console height.
        assert "${ssid}" in issue, issue
        assert "${psk}" in issue, issue

        # The QR itself is asserted against a stated budget rather than against
        # this VM's console, which is short enough that loom-issue drops the
        # code -- correctly, and the next subtest is what covers that. Pinning
        # the budget keeps this checking the rendering rather than the qemu
        # window's incidental size.
        code = appliance.succeed("LOOM_INFO_ROWS=60 loom-info")
        assert "Scan to join" in code, code
        # Drawn with the half blocks, not with '#'. An ASCII QR has modules
        # twice as tall as they are wide and phones refuse it -- see box.nix.
        assert "▀" in code or "▄" in code, code

        # The health check found a working AP, so it must not have left a
        # warning contradicting the credentials printed above it.
        appliance.wait_for_unit("loom-wifi-check.service")
        appliance.fail("test -e /run/issue.d/61-loom-wifi.issue")

    with subtest("the banner sheds content rather than overflowing the screen"):
        # agetty never pages the issue, and the row count is the panel's height
        # over the console cell -- anywhere from 33 rows to 123. So loom-info
        # drops what it can rather than letting the top scroll away. The order
        # matters more than the sizes: what goes is what carries no information.
        def banner(rows):
            return appliance.succeed(f"LOOM_INFO_ROWS={rows} loom-info")

        full = banner(0)
        assert "▄████▄    ▄████▄" in full, full     # the mark
        assert "Scan to join" in full, full          # the QR

        # Tall enough for everything.
        assert len(banner(60).splitlines()) == len(full.splitlines())

        # Too short for the mark, still room for the code.
        mid = banner(36)
        assert "▄████▄    ▄████▄" not in mid, mid
        assert "Scan to join" in mid, mid

        # Too short for the code either. It is a convenience, and the
        # credentials it encodes are still printed in full underneath.
        small = banner(24)
        assert "Scan to join" not in small, small
        assert "${ssid}" in small and "${psk}" in small, small

        for rows in [24, 36, 60]:
            got = len(banner(rows).splitlines())
            assert got <= rows - 3, f"{rows}-row console got a {got}-row banner"

    with subtest("the banner is redrawn after the console geometry settles"):
        # tty1 is painted while the font -- and with it the row count -- is
        # still changing under it; tty2 and up are spawned on demand, after it
        # has settled, which is why only tty1 came out cropped. This unit is
        # what closes that gap, started by branding.nix's font units.
        appliance.succeed("systemctl cat loom-banner-repaint.service")
        reapply = appliance.succeed("systemctl cat loom-console-font-reapply.service")
        assert "loom-banner-repaint.service" in reapply, reapply

        # It must refuse to act once somebody is logged in: a restart then
        # would take the operator's session with it. With no getty at the
        # banner in this VM, the run is a no-op and must still succeed.
        appliance.succeed("systemctl start loom-banner-repaint.service")

    with subtest("a radio that never appears is reported, not hidden"):
        # The failure this guards against is silent by construction: hostapd
        # BindsTo the radio's device unit, so a wrong match or a card that
        # cannot do AP mode simply leaves it inactive. Nothing fails, and the
        # banner would go on advertising a network that does not exist.
        appliance.succeed("ip link set loomwl0 name gone")
        appliance.succeed("systemctl restart loom-wifi-check.service")
        warning = appliance.succeed("cat /run/issue.d/61-loom-wifi.issue")
        assert "does not exist" in warning, warning
        assert "wired port still works" in warning, warning
  '';
}
