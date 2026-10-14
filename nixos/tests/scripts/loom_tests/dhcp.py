"""The default build's DHCP server: dnsmasq on loom0, on a box with no bridge.

Everything else in this package either forces dnsmasq off or, in wifi.py, reads a lease
off the --wifi bridge. This is the build that gets flashed, and the one where dnsmasq's
interface is a physical port renamed during boot rather than a bridge created by the
configuration -- which is why it was the build that broke.

Two distinct failures are covered, and they fail in opposite directions:

* The ordering. dnsmasq must not start before the address unit has run. Asserted as
  "it came up on the first attempt", not as "it is up now": Restart=on-failure means a
  box that lost the race can still look healthy a minute later, which is exactly how
  this shipped.
* The binding mode. bind-dynamic must survive an interface that is not there when
  dnsmasq starts -- asserted by taking the interface away and putting it back, rather
  than by hoping the boot reproduces the timing.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest

# The names portal.nix answers with the responder's own address, and two real
# sites it deliberately leaves alone. Restated here rather than read off
# `loom.portal.probeHosts`, as loom_tests/appliance/portal.py restates them: a
# test that took the list from the configuration it is checking would agree with
# whatever that list said.
PROBE_HOSTS = [
    "connectivitycheck.gstatic.com",
    "captive.apple.com",
    "www.msftconnecttest.com",
    "detectportal.firefox.com",
]
UNCLAIMED = ["www.google.com", "www.apple.com"]


class Params(NamedTuple):
    """The interface and the addresses the image was built with."""

    interface: str
    box_address: str
    portal_address: str
    pool_start: str


def _offer(appliance: "Machine", params: Params) -> dict[int, str]:
    """One DHCP offer from the appliance, as {option code: value}."""
    raw = appliance.succeed(f"loom-dhcp-probe {params.interface} {params.box_address}")

    # The address offered has to come out of the pool network.nix configured. The
    # probe already refuses an offer from any other server on the segment, so this
    # is the second half of that: the right server, handing out the right range.
    pool = params.pool_start.rsplit(".", maxsplit=1)[0]
    assert raw.splitlines()[0].startswith(f"yiaddr {pool}."), raw

    return {
        int(line.split()[1]): line.split()[2]
        for line in raw.splitlines()
        if line.startswith("option ")
    }


def _interface_claimed(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the wired port is claimed and both addresses land on it"):
        appliance.wait_for_unit("loom-interface-fallback.service")
        appliance.wait_for_unit(f"network-addresses-{params.interface}.service")

        # Both, and out of one unit: the second is the captive portal responder's,
        # and nginx is ordered on that same unit for it (portal.nix).
        addrs = appliance.succeed(f"ip -4 addr show {params.interface}")
        assert f"{params.box_address}/24" in addrs, addrs
        assert f"{params.portal_address}/24" in addrs, addrs


def _dnsmasq_came_up_first_time(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("dnsmasq came up on the first attempt, not on a retry"):
        # The assertion this whole test exists for. nixpkgs orders dnsmasq after
        # network.target and nothing else, and under this pin
        # network-addresses-<iface>.service is deliberately not part of
        # network.target -- so without the edges network.nix adds, dnsmasq starts
        # before the address exists and exits "unknown interface".
        #
        # Restart=on-failure then makes the symptom intermittent rather than
        # obvious: five failures inside ten seconds and the unit stays dead, but a
        # slower boot can leave it running and looking fine. NRestarts is what
        # tells the two apart, and it is zero on a box that was ordered correctly.
        appliance.wait_for_unit("dnsmasq.service")
        restarts = appliance.succeed(
            "systemctl show -p NRestarts --value dnsmasq.service"
        ).strip()
        assert restarts == "0", appliance.succeed("journalctl -b -u dnsmasq.service")


def _lease(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("a client on the wire gets a lease, from this box"):
        # The field symptom was "no DHCP", so this is the assertion that matches
        # it. An active dnsmasq is not the same thing: with bind-dynamic the
        # daemon starts whether or not its `interface=` ever matched anything.
        options = _offer(appliance, params)
        assert options.get(6) == params.box_address, options  # dns-server
        assert options.get(1) == "255.255.255.0", options  # netmask

        # No gateway, for the reason network.nix spells out: the box is an island,
        # and a lease naming it as the default route takes a visitor's laptop off
        # the internet on every interface it has.
        assert 3 not in options, options


def _wildcard_dns(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("*.loom resolves through the box's own resolver"):
        # Asked of the resolver at the appliance address rather than through
        # /etc/hosts, because that is what a client the box has just leased to
        # will use.
        #
        # -t A on purpose: a bare `host` also asks for AAAA and MX, and dnsmasq
        # refuses both -- `address=/loom/<ipv4>` synthesises A records only and
        # there is no upstream to forward the rest to.
        answer = appliance.succeed(f"host -t A frontend.loom {params.box_address}")
        assert f"has address {params.box_address}" in answer, answer


def _probe_names(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest(
        "the captive-portal probes resolve to the responder, and nothing else"
    ):
        # Moved here from loom_tests/appliance/portal.py, which could only grep
        # the rendered configuration: tests/appliance.nix forces dnsmasq off, so
        # that node has no dnsmasq.service and no config file to read. This node
        # runs the resolver, so the decision can be asked rather than inferred --
        # which is the same argument tests/dhcp-probe.nix makes about the lease.
        for host in PROBE_HOSTS:
            answer = appliance.succeed(f"host -t A {host} {params.box_address}")
            assert f"has address {params.portal_address}" in answer, answer

        # The fallbacks portal.nix deliberately does not claim. They are real
        # sites, and hijacking them would turn an answer to a question only an OS
        # asks into blanket interception -- so their absence is as much the
        # decision as the four entries are.
        #
        # REFUSED rather than an answer, because there is no upstream (no-resolv)
        # and no wildcard: a `address=/#/` would make every one of these resolve
        # to the box and this subtest is what would catch it.
        for host in UNCLAIMED:
            appliance.fail(f"host -t A {host} {params.box_address}")


def _portal_responder(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the portal responder holds port 80 on the second address"):
        # The sibling of the dnsmasq assertion, and the reason the bug was
        # survivable at all: portal.nix has ordered nginx on this very address
        # unit since it was written, and network.nix did not. Both now do, and
        # both are checked, so they cannot drift apart again.
        appliance.wait_for_unit("nginx.service")

        # With the probe's own Host header, because that is what decides which of
        # the two server blocks on this socket answers. A probe matches no
        # `server_name`, falls to the default server and is redirected; a request
        # that names the address is the visitor who typed it, and gets the page.
        # Fetching a probe path without the header tests neither.
        probe = appliance.succeed(
            "curl --silent --include "
            "--header 'Host: connectivitycheck.gstatic.com' "
            f"http://{params.portal_address}/generate_204"
        )
        assert "302" in probe, probe


def _survives_a_missing_interface(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest(
        "dnsmasq starts without the interface and picks it up when it returns"
    ):
        # The other half of the fix, asserted directly rather than left to the
        # boot to reproduce. With bind-interfaces, dnsmasq resolves `interface=`
        # once at startup and exits "unknown interface loom0" -- the message a
        # 1.5.0-rc4 box left in its journal. bind-dynamic starts anyway and
        # listens once the interface appears.
        #
        # Last, because it leaves the box perturbed: the interface is renamed out
        # from under the running daemon and put back by hand, not by the address
        # unit, whose .device went away with it.
        #
        # The addresses ride along with the netdev rather than being dropped --
        # a rename changes the name, not what is configured on it -- so nothing
        # has to be re-added afterwards. What goes away and comes back is the
        # name dnsmasq was told to answer on, which is the thing under test.
        appliance.succeed(f"ip link set {params.interface} down")
        appliance.succeed(f"ip link set {params.interface} name gone")

        # Starts, rather than exiting the way bind-interfaces did. dnsmasq logs
        # "error binding DHCP socket to device loom0" here and carries on; that
        # message in the journal is the daemon coping, not the daemon failing.
        appliance.succeed("systemctl restart dnsmasq.service")
        appliance.wait_for_unit("dnsmasq.service")

        appliance.succeed(f"ip link set gone name {params.interface}")
        appliance.succeed(f"ip link set {params.interface} up")

        # No restart between here and the offer. That is the assertion: the probe
        # is retried rather than the daemon, so a lease coming back means dnsmasq
        # bound an interface that appeared after it had started.
        appliance.wait_until_succeeds(
            f"loom-dhcp-probe {params.interface} {params.box_address}"
        )


def run(
    appliance: "Machine", *, start_all: "StartAll", subtest: "Subtest", params: Params
) -> None:
    """The whole test, as the .nix file calls it.

    The order is load-bearing at one end: the last subtest renames the interface out
    from under the running daemon and puts the address back by hand. Nothing that reads
    the boot's own state may follow it.
    """
    start_all()
    appliance.wait_for_unit("multi-user.target")

    _interface_claimed(appliance, subtest, params)
    _dnsmasq_came_up_first_time(appliance, subtest)
    _lease(appliance, subtest, params)
    _wildcard_dns(appliance, subtest, params)
    _probe_names(appliance, subtest, params)
    _portal_responder(appliance, subtest, params)
    _survives_a_missing_interface(appliance, subtest, params)
