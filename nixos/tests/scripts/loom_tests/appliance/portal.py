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
    no space after it and a hash character before it. A bare search for the flag matches
    that first and returns the rest of the PATH as a filename.
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

        # Outside the DHCP pool, or the box would hand a visitor one of these two
        # addresses and the lease would collide with a listener.
        #
        # Read off `LOOM_DHCP_POOL`, which network.nix writes into the same file,
        # rather than from a pool constructed here out of the same parameter the
        # reserved addresses are: that would compare two literals and consult
        # nothing about the box.
        pool = re.search(r"^LOOM_DHCP_POOL=(\S+)-(\S+)$", conf, re.M)
        assert pool, conf
        low, high = (int(end.rsplit(".", maxsplit=1)[-1]) for end in pool.groups())
        for reserved in (box, portal):
            host = int(reserved.rsplit(".", maxsplit=1)[-1])
            assert not low <= host <= high, f"{reserved} is inside {pool.group(0)}"


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
        #
        # And the literal address rather than `portal.loom`: a redirect to a name
        # makes the webview resolve a TLD that does not exist, and on a phone with
        # Android's Private DNS in strict mode that cannot succeed at all. Such a
        # phone still detects the portal -- the connectivity check bypasses private
        # DNS -- and then cannot follow the redirect.
        assert f"return 302 http://{portal}/" in nginx_conf, nginx_conf
        assert f"return 302 http://{page}/" not in nginx_conf, nginx_conf
        assert f"https://{page}" not in nginx_conf, nginx_conf

        # 302, never 301: these URLs belong to Google and Apple, and a permanent
        # redirect is cached -- a phone that kept this one would go on believing
        # connectivitycheck.gstatic.com is Loom long after leaving the appliance.
        assert "return 301" not in nginx_conf, nginx_conf

        # Exactly one of the server blocks on that socket is the default, and that
        # is what decides a probe: it arrives with a Host no `server_name` matches,
        # falls to the default server and is redirected. Give the page
        # `default_server` as well and every probe path starts answering 200 --
        # which is the one failure this whole mechanism exists to avoid, and one
        # nothing else here can see. tests/appliance-portal.nix sends the request.
        #
        # **This is the invariant**, not the count below it: the number of blocks
        # on the socket is three today (the catch-all, the page, and the two Linux
        # desktop probes that can only be told apart by Host) and will change again.
        assert nginx_conf.count(f"listen {portal}:80 default_server") == 1, nginx_conf
        assert nginx_conf.count(f"listen {portal}:80") == 3, nginx_conf
        assert f"server_name {page} {portal} ;" in nginx_conf, nginx_conf

        # And the page is proxied rather than served from a root: the certificate it
        # hands out and the answers it gives change with the cluster, so it is a
        # process rather than a directory.
        assert "proxy_pass http://127.0.0.1:18082;" in nginx_conf, nginx_conf

        # Every proxied location says who the client is, and that is a forgery
        # guard rather than plumbing: a header written only where it is true is a
        # header somebody can set where it is not. The same rule the `X-Loom-Secure`
        # note in portal.nix states.
        # Counted on the prefix, not on the whole directive: the Ubuntu and KDE
        # vhost's `proxy_pass` carries a path, because it rewrites `/` on the way
        # to the page server, and an exact match would quietly not count it --
        # which would make this assertion pass while saying nothing.
        assert nginx_conf.count(
            "proxy_set_header X-Loom-Client $remote_addr;"
        ) == nginx_conf.count("proxy_pass http://127.0.0.1:18082"), nginx_conf

        # The probe paths are proxied so a client that pressed the button on the
        # page can be told what its vendor wants to hear -- and each of them falls
        # back to the catch-all's own redirect if the page server is not there, so
        # a probe never sees an nginx error page inside a captive sheet.
        probe_locations = nginx_conf.count("error_page 502 503 504 = @probe_fallback;")
        assert probe_locations >= 11, nginx_conf
        assert "location @probe_fallback" in nginx_conf, nginx_conf

        # Ubuntu's and KDE's probes both fetch `/`, which on every other listener is
        # the page -- so that vhost rewrites the URI on the way to the page server
        # rather than passing it through. Without the rewrite a NetworkManager probe
        # is answered with the whole portal page at status 200, which is the one
        # answer a probe must never get.
        assert "server_name connectivity-check.ubuntu.com networkcheck.kde.org" in (
            nginx_conf
        ), nginx_conf
        assert (
            "proxy_pass http://127.0.0.1:18082/generate_204;" in nginx_conf
        ), nginx_conf
        assert "limit_req_zone  $binary_remote_addr zone=loom_portal_probe" in (
            nginx_conf
        ), nginx_conf

        # `location /` stays a static return, on the catch-all and on the probe
        # vhost, and so does each of their fallbacks -- four in all. It answers every
        # hostname on the segment now that the resolver is a wildcard, and a static
        # return has no upstream, no connect, no timeout and no failure mode. The
        # count is what would catch somebody proxying it wholesale, which is the
        # obvious implementation and the one this design is built around not taking.
        assert nginx_conf.count(f"return 302 http://{portal}/") == 4, nginx_conf


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
