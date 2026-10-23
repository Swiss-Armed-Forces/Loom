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

# The names portal.nix answers with the responder's own address by name.
# Restated here rather than read off `loom.portal.probeHosts`, as
# loom_tests/appliance/portal.py restates them: a test that took the list from
# the configuration it is checking would agree with whatever that list said.
PROBE_HOSTS = [
    "connectivitycheck.gstatic.com",
    "captive.apple.com",
    "www.msftconnecttest.com",
    "detectportal.firefox.com",
]

# Names nothing in the configuration mentions, which is the point: these reach
# the responder through the wildcard or not at all. A vendor probe nobody listed
# used to be REFUSED, and a client that cannot resolve its probe concludes "no
# internet" rather than "portal present" -- so the refusal was the bug, not the
# tidiness it looked like.
WILDCARD_HOSTS = [
    "www.google.com",  # the AOSP https probe, and its gen_204 fallback
    "connectivitycheck.android.com",  # another AOSP fallback
    "captive.samsung.com",  # Samsung's own
    "connect.rom.miui.com",  # Xiaomi's
    "nmcheck.gnome.org",  # GNOME
    "networkcheck.kde.org",  # KDE
]

# The carve-outs that must answer NXDOMAIN rather than the portal, each because
# something specified it that way.
NXDOMAIN_HOSTS = [
    # Mozilla's canary: anything but NOERROR-with-records turns DNS-over-HTTPS
    # off for a client that has it on by default. The wildcard would hand it a
    # positive answer and leave DoH on, pointed at an endpoint this box resets.
    "use-application-dns.net",
    # Apple's signal that a network does not permit iCloud Private Relay. Under
    # the wildcard it resolves and Private Relay fails obscurely instead.
    "mask.icloud.com",
    "mask-h2.icloud.com",
    # The one single-label name a Windows client looks up unprompted.
    "wpad",
]

# What Windows compares against before it will probe over http at all.
NCSI_PROBE = "dns.msftncsi.com"
NCSI_EXPECTED = "131.107.255.255"


class Params(NamedTuple):
    """The interface and the addresses the image was built with."""

    interface: str
    box_address: str
    portal_address: str
    pool_start: str
    pool_end: str


class Offer(NamedTuple):
    """The three options a lease from this box is judged on.

    Named rather than the raw {option code: value} map it is read out of: the codes are
    the wire's spelling, and an assertion written as `options.get(6)` needs a table
    beside it to say that 6 is the resolver and 3 the gateway.
    """

    netmask: str | None
    """Option 1."""

    gateway: str | None
    """Option 3 -- the box's own address is the correct answer; see `_lease`."""

    dns_server: str | None
    """Option 6."""


def _offer(appliance: "Machine", params: Params) -> Offer:
    """One DHCP offer from the appliance."""
    raw = appliance.succeed(f"loom-dhcp-probe {params.interface} {params.box_address}")

    # The address offered has to come out of the pool network.nix configured. The
    # probe already refuses an offer from any other server on the segment, so this
    # is the second half of that: the right server, handing out the right range.
    #
    # The last octet, not the /24 prefix. Comparing prefixes accepted any address
    # on the segment -- including the box's own and the portal responder's, which
    # is the collision `appliance-units.nix` calls out in prose and which nothing
    # else in this suite covers.
    offered = raw.splitlines()[0].split()[1]
    low, high = (
        int(end.rsplit(".", maxsplit=1)[-1])
        for end in (params.pool_start, params.pool_end)
    )
    prefix = params.pool_start.rsplit(".", maxsplit=1)[0]
    assert offered.startswith(f"{prefix}."), raw
    assert low <= int(offered.rsplit(".", maxsplit=1)[-1]) <= high, raw
    assert offered not in (params.box_address, params.portal_address), raw

    options = {
        int(line.split()[1]): line.split()[2]
        for line in raw.splitlines()
        if line.startswith("option ")
    }
    return Offer(
        netmask=options.get(1), gateway=options.get(3), dns_server=options.get(6)
    )


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
        offer = _offer(appliance, params)
        assert offer.dns_server == params.box_address, offer
        assert offer.netmask == "255.255.255.0", offer

        # The gateway, which this test used to assert the absence of.
        #
        # Naming the box as the default route does take a cabled laptop off the
        # internet, which is why it was suppressed -- but a client with no route
        # to this box sends its captive-portal probe out of some other interface,
        # where it succeeds, and is never offered the sign-in. network.nix has
        # the whole argument; this is the half that fails if somebody takes the
        # option back out.
        assert offer.gateway == params.box_address, offer


def _wildcard_dns(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("*.loom resolves through the box's own resolver"):
        # Asked of the resolver at the appliance address rather than through
        # /etc/hosts, because that is what a client the box has just leased to
        # will use.
        #
        # -t A on purpose: a bare `host` also asks for AAAA and MX, which are a
        # separate assertion below.
        answer = appliance.succeed(f"host -t A frontend.loom {params.box_address}")
        assert f"has address {params.box_address}" in answer, answer

        # And the longest match still wins over the wildcard. This is the
        # assertion that catches `address=/#/` swallowing `.loom`, which would
        # send every visitor's frontend.loom at the portal responder instead of
        # at Traefik -- a box that serves a captive portal page and no Loom.
        page = appliance.succeed(f"host -t A portal.loom {params.box_address}")
        assert f"has address {params.portal_address}" in page, page


def _no_data_rather_than_refused(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a query an A record cannot answer is NODATA, not REFUSED"):
        # What `local=/#/` is for, and the reason it is not optional.
        #
        # dnsmasq(8) says that since 2.86 a query whose type the `address=`
        # literal cannot answer "is sent upstream" -- and there is no upstream
        # (`no-resolv`), so it comes back REFUSED. A REFUSED AAAA beside a good A
        # is a lookup some client stacks fail whole, and under the wildcard that
        # would be every name on the segment rather than just `.loom`.
        #
        # `host` exits 1 and prints `5(REFUSED)` without it, so this
        # distinguishes the two precisely rather than merely noticing an error.
        answer = appliance.succeed(f"host -t AAAA frontend.loom {params.box_address}")
        assert "has no AAAA record" in answer, answer


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

        # And the names nothing in the configuration mentions, which the
        # wildcard answers. These used to be REFUSED on the grounds that
        # hijacking a real site is blanket interception -- which it is, and the
        # cost of not doing it was that a Samsung or Xiaomi phone probed a name
        # this box refused and concluded there was no internet rather than a
        # portal.
        for host in WILDCARD_HOSTS:
            answer = appliance.succeed(f"host -t A {host} {params.box_address}")
            assert f"has address {params.portal_address}" in answer, answer

        # Three carve-outs that have to be NXDOMAIN rather than the portal, each
        # because somebody specified it that way. See the lists above.
        for host in NXDOMAIN_HOSTS:
            appliance.fail(f"host -t A {host} {params.box_address}")

        # And the one carve-out that has to be a specific literal: Windows
        # compares this answer before it will send its http probe at all, so
        # handing it the responder makes Windows 10 show the globe and never
        # offer a sign-in.
        ncsi = appliance.succeed(f"host -t A {NCSI_PROBE} {params.box_address}")
        assert f"has address {NCSI_EXPECTED}" in ncsi, ncsi


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

        # No restart between here and the offer. That is the assertion -- and it
        # is now made: `dnsmasq.service` carries `Restart=on-failure`, so a
        # daemon that exited "unknown interface" would be restarted by systemd
        # and would bind cleanly the moment the name came back, with
        # `wait_until_succeeds` then getting its lease and the test passing
        # having proved the opposite of what it claims.
        restarts_before = _restarts(appliance)
        appliance.wait_until_succeeds(
            f"loom-dhcp-probe {params.interface} {params.box_address}"
        )
        assert _restarts(appliance) == restarts_before, (
            "dnsmasq was restarted before it answered; it did not bind the "
            "interface that appeared under it"
        )


def _restarts(appliance: "Machine") -> int:
    """How many times systemd has restarted dnsmasq on this boot."""
    return int(
        appliance.succeed("systemctl show -p NRestarts --value dnsmasq.service").strip()
    )


def _a_client_on_the_wire(
    appliance: "Machine", visitor: "Machine", subtest: "Subtest", params: Params
) -> None:
    """The three things a real client depends on, asserted from a real client.

    Everything else in this suite runs on the appliance, which proves the box answers a
    request somebody crafted and says nothing about whether a visitor's laptop ever gets
    to send one. That gap is how the captive portal shipped undetectable on every client
    anyone tried it with.
    """
    # The DNAT catch-all rules live in `loom-expose`, which requires docker, so
    # rules can land well after multi-user.target on a cold VM. Waited for here
    # rather than at the top of `run`, because nothing before this subtest needs
    # them.
    appliance.wait_for_unit("loom-expose.service")
    visitor.wait_for_unit("network.target")

    with subtest("a client that ignores the lease's resolver still reaches the page"):
        # The backstop the whole portal rests on. DNS interception only works for
        # a client willing to use the resolver it was given, and a phone with an
        # MDM profile, a hardcoded 8.8.8.8 or an encrypted-DNS setting is not --
        # so port 53 is DNAT'd to the box whatever the client aimed at.
        answer = visitor.succeed("host -t A frontend.loom 8.8.8.8")
        assert f"has address {params.box_address}" in answer, answer

    with subtest("a probe to an address nobody intercepted still lands on the page"):
        # And the other half of it: every vendor's connectivity probe is plaintext
        # http, so port 80 is DNAT'd to the responder whatever address the client
        # resolved. 198.51.100.7 is TEST-NET-2 and is not on this segment, so the
        # only thing that can answer is the catch-all.
        headers = visitor.succeed(
            "curl --silent --show-error --max-time 10 --head "
            "--header 'Host: connectivitycheck.gstatic.com' http://198.51.100.7/"
        )
        assert "302" in headers.splitlines()[0], headers
        assert f"Location: http://{params.portal_address}/" in headers, headers

    with subtest("everything else off the segment is refused rather than dropped"):
        # The lease names the box as the default route, so this node's off-subnet
        # traffic arrives there to be told no -- and it has to be told quickly.
        # A drop is a thirty-second hang in a browser tab; the REJECT plus the two
        # ICMP rate limits network.nix lifts make it immediate.
        #
        # docker0's subnet rather than minikube's: the bridge the cluster would
        # create does not exist in a test VM, and this is a network the box can
        # actually route to, which is exactly the traffic the blackhole exists to
        # stop. Without it docker's own chain accepts a forwarded packet to any
        # published container port -- the kube-apiserver included, which is the
        # port asked for here.
        #
        # Deliberately not port 80, which is the one port this cannot be tested
        # on: the catch-all above DNATs it to the portal from anywhere, so a
        # request there is answered rather than refused. That is the subtest
        # before this one.
        visitor.fail("curl --silent --max-time 5 https://172.17.0.2:8443/")

        # And it was refused, not ignored. `ping` reports the ICMP, which is the
        # difference this asserts; a dropped packet times out silently instead.
        #
        # `Host Unreachable` exactly, and not any unreachable: the kernel emits
        # `Net Unreachable` of its own accord when the box has no route at all,
        # so the looser match would pass whether or not the REJECT rule is there
        # -- it would assert the sysctls and nothing else. This wording is the
        # one `--reject-with icmp-host-unreachable` produces.
        reply = visitor.succeed("ping -c 1 -W 5 172.17.0.2 || true")
        assert "Host Unreachable" in reply, reply


def run(
    appliance: "Machine",
    visitor: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
    params: Params,
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
    _no_data_rather_than_refused(appliance, subtest, params)
    _probe_names(appliance, subtest, params)
    _portal_responder(appliance, subtest, params)
    _a_client_on_the_wire(appliance, visitor, subtest, params)
    _survives_a_missing_interface(appliance, subtest, params)
