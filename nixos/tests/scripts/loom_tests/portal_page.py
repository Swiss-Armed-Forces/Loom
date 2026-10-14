"""The captive portal page, on a booted box with no cluster behind it.

That is the realistic state, not a contrived one: a bring-up takes minutes on a good day
and hours on a first-time setup, and the page is up from the moment nginx is. Everything
here is therefore about a box that cannot issue anything yet and has to say so.

What this covers that nothing else can:

* **nginx is running at all.** On a `--require-client-cert` image it once was not. The
  nixpkgs unit runs as the `nginx` user and `nginx -t` in its `preStart` opens every
  certificate named in the configuration, so a key the service user cannot read takes
  down the captive portal, the Ollama proxy and USB ingest together -- silently, at boot,
  on hardware.
* **A probe is still a redirect.** `loom_tests/appliance/portal.py` reads that decision
  out of the rendered configuration; this one sends the request. The difference matters
  because vhost selection is nginx's, not ours: the catch-all answers because the probe's
  Host matches no `server_name`, and that is a property of two server blocks together.
* **The two listeners differ in what they offer.** The form appears on the TLS one and
  not on the plaintext one, which is the whole of why there are two.

The half that needs a cluster -- that a certificate actually comes back -- stays a manual
check on hardware (Documentation/appliance.md). What is checked here instead is that the
box says "Loom is still starting" rather than hanging, which is the answer every visitor
gets for the first hours of a box's life.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest

# One real probe path per vendor. Restated rather than read off the configuration, for
# the reason loom_tests/appliance/portal.py gives: a test that took the list from the
# thing it is checking would agree with whatever that list said.
PROBE_PATHS = [
    "/generate_204",
    "/hotspot-detect.html",
    "/connecttest.txt",
    "/success.txt",
]

# What `curl` is given for every call. `--max-time` because the one failure mode worth
# naming is a page that hangs instead of answering, and a hung test reads as a timeout
# forty minutes later with nothing to show for it.
CURL = "curl --silent --show-error --max-time 20"


class Params(NamedTuple):
    """The addresses and names the image was built with."""

    portal_address: str
    portal_host: str
    frontend_host: str


def _status(appliance: "Machine", command: str) -> str:
    return appliance.succeed(
        f"{command} --output /dev/null --write-out '%{{http_code}}'"
    )


def run(
    appliance: "Machine",
    start_all: "StartAll",
    subtest: "Subtest",
    params: Params,
) -> None:
    start_all()
    appliance.wait_for_unit("multi-user.target")

    _nginx_is_up(appliance, subtest, params)
    _probes_still_redirect(appliance, subtest, params)
    _the_page_is_served(appliance, subtest, params)
    _the_anchor_is_honest_about_not_being_there(appliance, subtest, params)
    _the_form_is_only_on_the_secure_listener(appliance, subtest, params)
    _the_password_is_on_the_login_screen(appliance, subtest)
    _a_wrong_password_asks_the_box_for_nothing(appliance, subtest, params)
    _the_issuer_answers_rather_than_hangs(appliance, subtest, params)
    _issuance_is_rate_limited(appliance, subtest, params)
    _the_spool_is_not_readable_by_the_page(appliance, subtest)


def _nginx_is_up(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("nginx started, which on a mutual TLS box it once did not"):
        appliance.wait_for_unit("nginx.service")
        # Named explicitly, because this is the failure: `nginx -t` runs as the service
        # user during preStart and opens `proxy_ssl_certificate`, so a root-owned 0600
        # key inside a 0700 directory fails the whole unit.
        journal = appliance.succeed("journalctl --unit nginx.service --no-pager")
        assert "Permission denied" not in journal, journal

        # The portal address and not localhost, which is the point of pinning every
        # listener to it: port 80 on the *appliance* address is DNAT'd to the minikube
        # node before the routing decision, and nothing here binds the loopback except
        # the three private proxies.
        appliance.wait_for_open_port(80, addr=params.portal_address)
        appliance.wait_for_open_port(443, addr=params.portal_address)


def _probes_still_redirect(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a captive-portal probe is redirected, never answered"):
        for path in PROBE_PATHS:
            # Sent the way a phone sends it: to the responder's address, with a probe
            # hostname in the Host header. That Host is what makes the catch-all answer
            # rather than the page, and it is the whole mechanism.
            headers = appliance.succeed(
                f"{CURL} --head --header 'Host: connectivitycheck.gstatic.com' "
                f"http://{params.portal_address}{path}"
            )
            assert "302" in headers.splitlines()[0], f"{path}: {headers}"
            assert f"Location: http://{params.portal_host}/" in headers, headers
            # A permanent redirect would be cached, and a phone would go on believing
            # connectivitycheck.gstatic.com is Loom long after it left the appliance.
            assert "301" not in headers.splitlines()[0], headers


def _the_page_is_served(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the page itself answers, by name and by address"):
        for target in (params.portal_host, params.portal_address):
            body = appliance.succeed(f"{CURL} http://{target}/")
            assert "Loom appliance" in body, body
            assert "Open Loom" in body, body
            # The island property, from the other side of nginx: a page that reached for
            # a font would hang for the browser's connect timeout and then render
            # unstyled, on the first screen a visitor ever sees.
            assert "<script src=" not in body, body
            assert "<link" not in body, body


def _the_anchor_is_honest_about_not_being_there(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("with no cluster, the certificate download says so"):
        # 503 rather than 404: the file is missing because Loom has not come up, not
        # because this box has nothing to offer.
        assert (
            _status(appliance, f"{CURL} http://{params.portal_host}/loom-server-ca.pem")
            == "503"
        )
        body = appliance.succeed(
            f"{CURL} http://{params.portal_host}/loom-server-ca.pem"
        )
        assert "Not available yet" in body, body


def _the_form_is_only_on_the_secure_listener(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the certificate form is offered over TLS and nowhere else"):
        plain = appliance.succeed(f"{CURL} http://{params.portal_host}/")
        assert "<form" not in plain, plain
        # And it says where to go instead, which is the only way a visitor on the
        # plaintext listener ever reaches the form.
        assert f"https://{params.portal_host}/#identity" in plain, plain

        # `--insecure`, because what is being presented at this point in a box's life is
        # the one-day placeholder loom-portal-tls-placeholder wrote: the real pair
        # arrives with the cluster. A browser would click through the same warning.
        secure = appliance.succeed(f"{CURL} --insecure https://{params.portal_host}/")
        assert '<form method="post" action="/certificate">' in secure, secure
        assert 'name="password"' in secure, secure


def _the_password_is_on_the_login_screen(
    appliance: "Machine", subtest: "Subtest"
) -> None:
    with subtest("today's password is generated and shown on tty1"):
        # The file rather than the unit: the rotation is a `Type=oneshot` with no
        # `RemainAfterExit` -- so that its timer can restart it -- and a unit like that
        # is `inactive (dead)` the moment it has done its job.
        appliance.wait_for_file("/run/loom-portal/password")
        password = appliance.succeed("cat /run/loom-portal/password").strip()

        # Four EFF words with dots between them, and none of the two letters that move
        # between Latin layouts -- the same rule the --lock-key passphrase follows.
        assert password.count(".") == 3, password
        assert "y" not in password and "z" not in password, password

        fragment = appliance.succeed("cat /run/issue.d/62-loom-portal.issue")
        assert password in fragment, fragment
        # agetty reads a backslash in an issue file as the start of an escape of its own
        # and eats it, taking whatever follows with it.
        assert "\\" not in fragment, fragment

        # And the file the page reads is not world-readable: it is the credential.
        mode = appliance.succeed("stat --format=%a /run/loom-portal/password").strip()
        assert mode == "640", mode


def _a_wrong_password_asks_the_box_for_nothing(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("a wrong password never reaches the privileged half"):
        status = _status(
            appliance,
            f"{CURL} --insecure --data 'password=not-todays-password' "
            f"https://{params.portal_host}/certificate",
        )
        assert status == "403", status

        # The assertion that matters: no spool entry was created, so the root issuer was
        # never woken and no key was generated.
        pending = appliance.succeed("ls -A /run/loom-portal/requests").strip()
        assert pending == "", pending


def _the_issuer_answers_rather_than_hangs(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("with the right password and no cluster, the box says it is starting"):
        password = appliance.succeed("cat /run/loom-portal/password").strip()
        body = appliance.succeed(
            f"{CURL} --insecure --data 'password={password}&label=visitor' "
            f"https://{params.portal_host}/certificate"
        )

        # The root issuer deliberately does not wait for a bring-up -- mtls.nix's issuer
        # does, because nobody is watching it; here somebody is standing at a page.
        assert "Loom is still starting" in body, body

        # It ran, and it ran cleanly. "cluster not ready" is the most ordinary
        # answer this unit ever gives, and it must not leave a failed unit behind
        # for an operator to find: the page writes its own answer file and deletes
        # it the moment it appears, so anything the issuer does to that file after
        # creating it is a race it loses about half the time -- `set -e` aborts,
        # the EXIT trap writes a second answer, and the unit reports failure on a
        # request that was handled correctly.
        result = appliance.succeed(
            "systemctl show loom-portal-issue.service --property=Result --value"
        ).strip()
        assert result == "success", result

        journal = appliance.succeed(
            "journalctl --unit loom-portal-issue.service --no-pager"
        )
        assert journal.strip(), "the path unit never started the issuer"
        assert "No such file or directory" not in journal, journal
        assert appliance.succeed("ls -A /run/loom-portal/requests").strip() == ""
        assert appliance.succeed("ls -A /run/loom-portal/bundles").strip() == ""


def _issuance_is_rate_limited(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> None:
    with subtest("the route that costs a key generation is throttled"):
        # nginx is the first of the four bounds and the only one a visitor meets before
        # the password is even read. `limit_req ... rate=6r/m burst=3` lets a handful
        # through and then refuses, which is a 503 by default.
        statuses = [
            _status(
                appliance,
                f"{CURL} --insecure --data 'password=wrong' "
                f"https://{params.portal_host}/certificate",
            )
            for _ in range(8)
        ]
        assert "503" in statuses, statuses

        # And the server throttles on its own account, for anything that reaches it --
        # asserted against the loopback port, because nginx refuses the burst above
        # before the bucket in the service ever sees it.
        direct = [
            _status(
                appliance,
                f"{CURL} --header 'X-Loom-Secure: 1' --data 'password=wrong' "
                "http://127.0.0.1:18082/certificate",
            )
            for _ in range(14)
        ]
        assert "429" in direct, direct


def _the_spool_is_not_readable_by_the_page(
    appliance: "Machine", subtest: "Subtest"
) -> None:
    with subtest("the page server may use the spool and may not read it"):
        for directory in ("requests", "bundles"):
            mode = appliance.succeed(
                f"stat --format='%a %U:%G' /run/loom-portal/{directory}"
            ).strip()
            # 0730 root:loom-portal -- create, stat and unlink by name; never enumerate.
            # A compromise of the one process a visitor talks to therefore cannot list
            # other visitors' tokens.
            assert mode == "730 root:loom-portal", f"{directory}: {mode}"

        # And the service that uses it is not root, which is what makes the mode mean
        # anything.
        user = appliance.succeed(
            "systemctl show loom-portal.service --property=User --value"
        ).strip()
        assert user == "loom-portal", user
