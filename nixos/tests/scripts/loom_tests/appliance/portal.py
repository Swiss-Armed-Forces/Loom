"""The captive portal, as configured.

Read out of the rendered nginx configuration rather than exercised over a socket, and
deliberately so: tests/appliance.nix forces `loom.autoSelectInterface` off to assert the
opposite property -- that a VM whose only NIC is virtio comes up with no `loom0` -- so
this box has no appliance address for nginx to bind. What can be checked here is the
decision, which is the part that rots.

The resolver half lives in loom_tests/dhcp.py instead. It cannot be checked here at all:
this node also forces dnsmasq off, so there is no dnsmasq.service and no rendered config
to read. That test's node runs the resolver, so it asks it which address each captive-
portal probe resolves to rather than inferring it from a config file.

What cannot be checked here at all is the half that needs a cluster: that the frontend
answers 200 over plain http once Traefik is up. Bring-up takes hours, so that stays a
manual check on hardware (Documentation/appliance.md).

tests/appliance-portal.nix is the other half of this file: it boots a box that *does* have
the address, and sends the requests whose answers are only decided here. The two do not
overlap -- this one reads a decision, that one observes it.
"""

import re
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def _config_path(appliance: "Machine", unit: str, flag: str) -> str:
    """The config a unit is pointed at, through its ExecStart.

    Same indirection modes.py follows for the loom.service start script: the path is
    generated into the store, so nothing in the unit file can be matched against a name
    written here.

    The flag has to be delimited on both sides, which is not fussiness. `systemctl cat`
    prints the whole unit, `Environment=PATH=` included, and a NixOS unit's PATH always
    carries `/nix/store/<hash>-coreutils-<version>/bin` -- in which `-c` appears, with
    no space after it and a hash character before it. A bare search for the flag matched
    that first and returned the rest of the PATH as a filename.
    """
    execstart = appliance.succeed(f"systemctl cat {unit}")
    match = re.search(rf"(?<![\w-]){re.escape(flag)}\s+(\S+)", execstart)
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


def redirect(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the responder redirects to the portal page over plain http"):
        nginx_conf = appliance.succeed(
            f"cat {_config_path(appliance, 'nginx.service', '-c')}"
        )
        portal = f"{params.loom_subnet}.2"
        # Derived rather than spelled out, the way portal.nix derives it: a box built
        # with another domain would answer for another name.
        frontend = next(h for h in params.loom_hosts if h.startswith("frontend."))
        page = f"portal.{frontend.split('.', maxsplit=1)[1]}"

        # Bound to the portal address alone. nginx's default is every address the
        # box holds, which would put it on port 80 of the appliance address too.
        assert f"listen {portal}:80" in nginx_conf, nginx_conf

        # http, and this is the point of the whole feature: a portal webview is not
        # a browser -- it refuses an untrusted certificate outright with no way to
        # click through, and the appliance's is self-signed for a TLD no public CA
        # can ever issue for. An https target here would dead-end every visitor.
        assert f"return 302 http://{page}/" in nginx_conf, nginx_conf
        assert f"https://{page}" not in nginx_conf, nginx_conf

        # 302, never 301: these URLs belong to Google and Apple, and a permanent
        # redirect is cached -- a phone that kept this one would go on believing
        # connectivitycheck.gstatic.com is Loom long after leaving the appliance.
        assert "return 301" not in nginx_conf, nginx_conf

        # Two server blocks on that socket, and exactly one of them is the default.
        # That is what decides a probe: it arrives with a Host no `server_name`
        # matches, falls to the default server and is redirected. Give the page
        # `default_server` as well and every probe path starts answering 200 --
        # which is the one failure this whole mechanism exists to avoid, and one
        # nothing else here can see. tests/appliance-portal.nix sends the request.
        assert nginx_conf.count(f"listen {portal}:80") == 2, nginx_conf
        assert nginx_conf.count(f"listen {portal}:80 default_server") == 1, nginx_conf
        assert f"server_name {page} {portal} ;" in nginx_conf, nginx_conf

        # And the page is proxied rather than served from a root: the certificate it
        # hands out and the answers it gives change with the cluster, so it is a
        # process rather than a directory.
        assert "proxy_pass http://127.0.0.1:18082;" in nginx_conf, nginx_conf


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
