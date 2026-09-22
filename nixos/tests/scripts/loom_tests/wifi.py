"""The `--wifi` build: the access point, the bridge, and what the screen says.

loom_tests/appliance deliberately does not cover any of this: it forces off dnsmasq and
the static addresses, which are exactly what this one exercises on a bridge.
"""

from typing import TYPE_CHECKING, NamedTuple

from loom_tests import vt

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest


class Params(NamedTuple):
    """The credentials and the address the image was built with."""

    ssid: str
    psk: str
    box_address: str


def _radio_renamed(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the radio is renamed and hostapd owns it"):
        appliance.wait_for_unit("hostapd.service")
        appliance.succeed("test -e /sys/class/net/loomwl0")

        # The SSID that reaches the air is the one that was built in, not a
        # default left behind by the module.
        conf = appliance.succeed("cat /run/hostapd/loomwl0.hostapd.conf")
        assert f"ssid={params.ssid}" in conf, conf
        # Transition mode: both key managements present, so a WPA2-only phone
        # and a WPA3 one can both associate. A regression to plain SAE here
        # would lock out the older half of the visitors this feature is for.
        assert "SAE" in conf and "WPA-PSK" in conf, conf
        assert "bridge=loombr0" in conf, conf


def _bridge(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the bridge exists and carries the appliance address"):
        appliance.succeed("test -d /sys/class/net/loombr0/bridge")
        # hostapd enslaves its own interface; nothing in the Nix config does.
        appliance.succeed("test -e /sys/class/net/loombr0/brif/loomwl0")

        # The whole point of the bridge: the address, the DHCP server and the
        # resolver sit on it rather than on the wired NIC, so a client reaching
        # the box over the air is on the same network as one that plugged in.
        addrs = appliance.succeed("ip -4 addr show loombr0")
        assert f"{params.box_address}/24" in addrs, addrs
        appliance.wait_for_unit("dnsmasq.service")
        # Resolved through the box's own resolver, at the bridge address, which
        # is what a joining client will use -- not through /etc/hosts.
        #
        # -t A on purpose. A bare `host` also asks for AAAA and MX, and dnsmasq
        # refuses both: `address=/loom/<ipv4>` synthesises A records only and
        # there is no upstream to forward the rest to. That is how the appliance
        # has always answered; it makes `host` exit non-zero on a lookup that
        # actually succeeded.
        answer = appliance.succeed(f"host -t A frontend.loom {params.box_address}")
        assert f"has address {params.box_address}" in answer, answer

        # The console's net box follows the address onto the bridge. Read out of
        # the script rather than out of a running session, which this test never
        # opens -- tests/appliance.nix asserts the generated file on a box with
        # no bridge, so between them both branches of `loom.serviceInterface`
        # are covered. Pinning `loom0` here would graph the wired port only, and
        # on a box deployed for its access point that port is usually empty.
        btop = appliance.succeed(
            "cat $(readlink -f /run/current-system/sw/bin/loom-btop)"
        )
        assert "loombr0" in btop, btop


def _lease_carries_no_gateway(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a lease points at the resolver and at no gateway"):
        # The appliance is an island: it has no upstream, and a client that
        # took it for a default gateway would hand it every packet bound for
        # anywhere else -- which is what happened, silently, for as long as
        # nixos/network.nix trusted an omitted option:router to mean no router
        # option. Plugging a laptop in took that laptop off the internet.
        #
        # Read off a real offer rather than off the configuration file, for the
        # reason given where loom-dhcp-probe is built.
        offer = appliance.succeed(f"loom-dhcp-probe loombr0 {params.box_address}")

        options = {
            int(line.split()[1]): line.split()[2]
            for line in offer.splitlines()
            if line.startswith("option ")
        }
        assert 3 not in options, offer  # router
        assert options.get(6) == params.box_address, offer  # dns-server
        assert options.get(1) == "255.255.255.0", offer  # netmask

        # And the address offered is out of the pool network.nix configured.
        # The probe already refuses an offer from any other server on the
        # segment -- qemu's own runs one in here -- so this is the second half
        # of that: the right server, handing out the right range.
        pool = params.box_address.rsplit(".", 1)[0]
        yiaddr = offer.splitlines()[0]
        assert yiaddr.startswith(f"yiaddr {pool}."), offer


def _bridge_forwarding(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("bridge ports forward immediately"):
        # With STP off the kernel puts ports straight into forwarding, so the
        # default 15-second forward delay should never apply. Pinned and checked
        # because the failure mode is invisible from the box: a phone's first
        # DHCPDISCOVER is swallowed and it self-assigns a 169.254 address, which
        # looks like a broken access point rather than like a bridge timer.
        assert (
            appliance.succeed("cat /sys/class/net/loombr0/bridge/stp_state").strip()
            == "0"
        )
        assert (
            appliance.succeed("cat /sys/class/net/loombr0/bridge/forward_delay").strip()
            == "0"
        )


def _radios_state(appliance: "Machine", subtest: "Subtest") -> None:
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


def _login_credentials(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the login screen carries the credentials and a scannable QR"):
        appliance.wait_for_unit("loom-issue.service")
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        assert f"{params.ssid}" in issue, issue
        assert f"{params.psk}" in issue, issue

        # Asserted against the issue file itself, not against a loom-info run
        # with arguments that flatter it. The banner briefly measured the console
        # and trimmed itself to fit, and because the console is resized several
        # times during boot the reading was whatever the resize sequence happened
        # to be in the middle of -- which shipped a box whose login screen had
        # neither the mark nor the QR code on a console with room for both. What
        # goes into the file is the whole banner, always.
        assert "▄████▄    ▄████▄" in issue, issue
        assert "Scan to join" in issue, issue
        # Drawn with the half blocks, not with '#'. An ASCII QR has modules
        # twice as tall as they are wide and phones refuse it -- see box.nix.
        assert "▀" in issue or "▄" in issue, issue

        # The health check found a working AP, so it must not have left a
        # warning contradicting the credentials printed above it.
        appliance.wait_for_unit("loom-wifi-check.service")
        appliance.fail("test -e /run/issue.d/61-loom-wifi.issue")


def _banner_watcher(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("the banner watcher is running, not hung off the font units"):
        # It used to be started from loom-console-font-reapply's ExecStartPost.
        # udev runs that during coldplug, before any getty exists, so the repaint
        # it asked for found nothing on screen and never ran again -- which is
        # how tty1 kept a cropped banner while tty2 looked right. It is pulled in
        # by the boot now and watches the console itself.
        appliance.succeed("systemctl cat loom-banner-repaint.service")
        reapply = appliance.succeed("systemctl cat loom-console-font-reapply.service")
        assert "loom-banner-repaint" not in reapply, reapply
        assert (
            appliance.succeed(
                "systemctl show -p ActiveState --value loom-banner-repaint.service"
            ).strip()
            == "active"
        )


def _banner_survives_resize(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("a console resize does not leave the banner cropped"):
        # The bug this reproduces: tty1 is painted while the console is still
        # being resized -- kernel font, Cozette, the DRM driver's reset, Cozette
        # again -- and a VT that shrinks keeps the bottom of the screen and
        # discards the top. The mark goes first. tty2 and up never showed it,
        # because logind spawns them on demand once nothing is moving any more.
        #
        # `setfont -d` doubles the cell, which halves the row count: the same
        # shrink, on demand. Restoring the font afterwards is what
        # loom-console-font-reapply does, and leaves the console back at the size
        # it started -- which is why the watcher has to track that a resize
        # happened rather than compare the size it now reads.
        # The mark's own signature: two block groups with a gap. The QR code is
        # dense and irregular and never produces it, so this distinguishes "the
        # mark is on screen" from "some block glyph is on screen". It reads as
        # '#' rather than as U+2588 because a console cell holds a font index --
        # see loom_tests/vt.py, which owns that decoding for every test.
        mark = "######    ######"

        def marked() -> bool:
            return any(mark in line for line in vt.read(appliance).top(10, width=40))

        assert marked()

        appliance.succeed("setfont -d -C /dev/tty1 2>&1 || true")
        appliance.sleep(2)
        assert not marked(), vt.read(appliance).top(10, width=40)

        appliance.succeed(
            "/run/current-system/systemd/lib/systemd/systemd-vconsole-setup || true"
        )
        appliance.sleep(14)

        # The whole assertion: the banner was redrawn for the console that is
        # there now, rather than left as the tail of one drawn for a console
        # that no longer exists.
        assert marked(), vt.read(appliance).top(10, width=40)


def _missing_radio_reported(appliance: "Machine", subtest: "Subtest") -> None:
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


def run(
    appliance: "Machine", *, start_all: "StartAll", subtest: "Subtest", params: Params
) -> None:
    """The whole test, as the .nix file calls it."""
    start_all()
    appliance.wait_for_unit("multi-user.target")

    _radio_renamed(appliance, subtest, params)
    _bridge(appliance, subtest, params)
    _lease_carries_no_gateway(appliance, subtest, params)
    _bridge_forwarding(appliance, subtest)
    _radios_state(appliance, subtest)
    _login_credentials(appliance, subtest, params)
    _banner_watcher(appliance, subtest)
    _banner_survives_resize(appliance, subtest)
    _missing_radio_reported(appliance, subtest)
