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
  };
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-interface-fallback";

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

  testScript = ''
    start_all()

    for machine in (single, dual, disabled):
        machine.wait_for_unit("multi-user.target")

    with subtest("a single wired NIC is claimed as loom0"):
        single.wait_for_unit("loom-interface-fallback.service")
        single.succeed("test -e /sys/class/net/loom0")

        record = single.succeed("cat /run/loom/interface-fallback")
        assert "LOOM_FALLBACK_REASON=auto" in record, record
        # Nothing is left carrying the kernel-assigned name it arrived with.
        assert "LOOM_FALLBACK_INTERFACE=loom0" not in record, record

    with subtest("the claimed NIC is a real one, not a bridge or a radio"):
        # The selection excludes anything with a DEVTYPE, which is how a WWAN
        # modem -- ARPHRD_ETHER, real device, no wireless directory -- stays out.
        devtype = single.succeed(
            "cat /sys/class/net/loom0/uevent | grep -c '^DEVTYPE=' || true"
        ).strip()
        assert devtype == "0", f"loom0 has a DEVTYPE: {devtype}"
        single.succeed("test -e /sys/class/net/loom0/device")

    with subtest("the console says the NIC was claimed automatically"):
        single.wait_for_unit("loom-network-check.service")
        issue = single.succeed("cat /run/issue.d/60-loom-network.issue")
        assert "claimed automatically" in issue, issue
        # No backslashes: agetty eats them out of an issue file as escapes.
        assert "\\" not in issue, issue

    with subtest("re-running the fallback changes nothing"):
        before = single.succeed("cat /run/loom/interface-fallback")
        single.succeed("systemctl restart loom-interface-fallback.service")
        single.succeed("test -e /sys/class/net/loom0")
        assert single.succeed("cat /run/loom/interface-fallback") == before

    with subtest("with two wired NICs exactly one is claimed, and the other is offered"):
        dual.wait_for_unit("loom-interface-fallback.service")
        dual.succeed("test -e /sys/class/net/loom0")

        record = dual.succeed("cat /run/loom/interface-fallback")
        assert "LOOM_FALLBACK_REASON=auto" in record, record

        alternatives = [
            line.split("=", 1)[1]
            for line in record.splitlines()
            if line.startswith("LOOM_FALLBACK_ALTERNATIVES=")
        ][0].split()
        assert len(alternatives) == 1, record

        # The alternative is named on the console, because "move the cable" is
        # the whole recovery path for a box that came up on the wrong port.
        dual.wait_for_unit("loom-network-check.service")
        issue = dual.succeed("cat /run/issue.d/60-loom-network.issue")
        assert alternatives[0] in issue, issue
        assert "move the cable" in issue, issue

    with subtest("the choice is the lowest device path, not whatever udev finished first"):
        chosen_path = dual.succeed(
            "basename $(readlink -f /sys/class/net/loom0/device)"
        ).strip()
        other = [
            line.split("=", 1)[1]
            for line in dual.succeed("cat /run/loom/interface-fallback").splitlines()
            if line.startswith("LOOM_FALLBACK_ALTERNATIVES=")
        ][0].split()[0]
        other_path = dual.succeed(
            f"basename $(readlink -f /sys/class/net/{other}/device)"
        ).strip()
        assert chosen_path < other_path, f"picked {chosen_path}, lower was {other_path}"

    with subtest("switched off, nothing is claimed and the warning stands"):
        disabled.fail("test -e /sys/class/net/loom0")
        disabled.fail("systemctl cat loom-interface-fallback.service")

        disabled.wait_for_unit("loom-network-check.service")
        issue = disabled.succeed("cat /run/issue.d/60-loom-network.issue")
        assert "does not exist" in issue, issue
        assert "\\" not in issue, issue
  '';
}
