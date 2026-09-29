"""The captive portal, as configured.

Read out of the rendered dnsmasq and nginx configurations rather than exercised over a
socket, and deliberately so: tests/appliance.nix forces `loom.autoSelectInterface` off
to assert the opposite property -- that a VM whose only NIC is virtio comes up with no
`loom0` -- so this box has no appliance address for either daemon to bind. What can be
checked here is the decision, which is the part that rots.

What cannot be checked here at all is the half that needs a cluster: that
`http://frontend.loom/` answers 200 once Traefik is up. Bring-up takes hours, so that
stays a manual check on hardware (Documentation/appliance.md).
"""

import re
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest

# The fallbacks portal.nix deliberately does not claim. They are real sites, and
# hijacking them would turn an answer to a question only an OS asks into blanket
# interception -- so their absence is as much the decision as the four entries are.
UNCLAIMED = ["www.google.com", "www.apple.com"]


def _config_path(appliance: "Machine", unit: str, flag: str) -> str:
    """The config a unit is pointed at, through its ExecStart.

    Same indirection modes.py follows for the loom.service start script: the path is
    generated into the store, so nothing in the unit file can be matched against a name
    written here.
    """
    execstart = appliance.succeed(f"systemctl cat {unit}")
    match = re.search(rf"{re.escape(flag)}\s*(\S+)", execstart)
    assert match, execstart
    return match.group(1)


def addresses(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the portal has an address of its own, beside the appliance's"):
        # It needs one. loom-expose DNATs ports 80 and 443 on the appliance address
        # to the minikube node in nat PREROUTING, ahead of the routing decision that
        # would hand a packet to a local listener -- so a responder sharing that
        # address could never be reached, and a probe sent there lands on Traefik,
        # which answers 404 for a Host it does not route.
        conf = appliance.succeed("cat /etc/loom/network.conf")
        box = f"{params.loom_subnet}.1"
        portal = f"{params.loom_subnet}.2"

        assert f"LOOM_BOX_ADDRESS={box}" in conf, conf
        assert f"LOOM_PORTAL_ADDRESS={portal}" in conf, conf

        # Below the DHCP pool, or the box would hand a visitor the responder's
        # address and the lease would collide with it.
        pool_start = int(f"{params.loom_subnet}.100".rsplit(".", maxsplit=1)[-1])
        assert int(portal.rsplit(".", maxsplit=1)[-1]) < pool_start, conf


def probe_names(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("dnsmasq sends the probes to the portal and refuses everything else"):
        dnsmasq_conf = appliance.succeed(
            f"cat {_config_path(appliance, 'dnsmasq.service', '-C')}"
        )
        box = f"{params.loom_subnet}.1"
        portal = f"{params.loom_subnet}.2"

        # The four dedicated probe FQDNs, at the responder rather than at the box.
        for host in [
            "connectivitycheck.gstatic.com",
            "captive.apple.com",
            "www.msftconnecttest.com",
            "detectportal.firefox.com",
        ]:
            assert f"address=/{host}/{portal}" in dnsmasq_conf, dnsmasq_conf

        # And nothing beyond them. A wildcard here would point a visitor's mail
        # client at this box instead of letting it fail cleanly, which is the whole
        # reason the list is written out one name at a time.
        for host in UNCLAIMED:
            assert host not in dnsmasq_conf, dnsmasq_conf
        assert "address=/#/" not in dnsmasq_conf, dnsmasq_conf

        # The names the box actually serves still resolve to the box.
        assert f"address=/loom/{box}" in dnsmasq_conf, dnsmasq_conf

        # No upstream, so everything else stays REFUSED rather than gaining an
        # answer as a side effect of the entries above.
        assert "no-resolv" in dnsmasq_conf, dnsmasq_conf


def redirect(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the responder redirects to the frontend over plain http"):
        nginx_conf = appliance.succeed(
            f"cat {_config_path(appliance, 'nginx.service', '-c')}"
        )
        portal = f"{params.loom_subnet}.2"
        frontend = next(h for h in params.loom_hosts if h.startswith("frontend."))

        # Bound to the portal address alone. nginx's default is every address the
        # box holds, which would put it on port 80 of the appliance address too.
        assert f"listen {portal}:80" in nginx_conf, nginx_conf

        # http, and this is the point of the whole feature: a portal webview is not
        # a browser -- it refuses an untrusted certificate outright with no way to
        # click through, and the appliance's is self-signed for a TLD no public CA
        # can ever issue for. An https target here would dead-end every visitor.
        assert f"return 302 http://{frontend}/" in nginx_conf, nginx_conf
        assert f"https://{frontend}" not in nginx_conf, nginx_conf

        # 302, never 301: these URLs belong to Google and Apple, and a permanent
        # redirect is cached -- a phone that kept this one would go on believing
        # connectivitycheck.gstatic.com is Loom long after leaving the appliance.
        assert "return 301" not in nginx_conf, nginx_conf


def http_entrypoint(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("loom.service asks up.sh to serve the frontend over http"):
        # Without this the redirect above lands on a Traefik that has no router on
        # port 80 for the host, and the visitor gets a 404 instead of Loom. The two
        # halves are only useful together, so they are asserted together.
        unit = appliance.succeed("systemctl cat loom.service")
        match = re.search(r"ExecStart=(\S+)", unit)
        assert match, unit
        start_script = appliance.succeed(f"cat {match.group(1)}")
        assert "--enable-http" in start_script, start_script
