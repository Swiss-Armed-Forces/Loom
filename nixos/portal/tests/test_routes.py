"""The probe contract.

This is the test that matters most in the package, and the reason `routes.py` is a
module of its own.

Every operating system decides whether a network reaches the internet by fetching a URL
whose answer it already knows, and reads a `204` or an expected body as "there is
internet here". If this page ever answered 200 at one of those paths, Android would stop
offering "Sign in to network", keep using mobile data, and resolve `frontend.loom`
against a mobile network that has never heard of `.loom`. Nothing about that is visible
from a browser, from `curl`, or from any other test in this repository -- it is a phone,
on a site, deciding quietly.

So: no path this router has never heard of resolves to the page. The nginx catch-all in
portal.nix answers the probes with a 302 before anything reaches this process at all;
this is the second half of that, for the case where something dials the loopback port.
"""

import pytest

from loom_portal.http import Request
from loom_portal.routes import Route, resolve

# The paths the four intercepted probe hostnames are actually fetched with, plus the
# variants that have appeared across OS releases. None of them may be the page.
PROBE_PATHS = [
    "/generate_204",  # Android, connectivitycheck.gstatic.com
    "/gen_204",  # Android, older
    "/hotspot-detect.html",  # iOS and macOS, captive.apple.com
    "/library/test/success.html",  # iOS, older
    "/success.txt",  # Firefox, detectportal.firefox.com
    "/connecttest.txt",  # Windows, www.msftconnecttest.com
    "/ncsi.txt",  # Windows, older
    "/redirect",  # Windows, www.msftconnecttest.com
    "/canonical.html",  # Ubuntu NetworkManager
    "/check_network_status.txt",  # ChromeOS
]


def get(path: str) -> Request:
    return Request(method="GET", path=path)


@pytest.mark.parametrize("path", PROBE_PATHS)
def test_a_probe_path_is_never_the_page(path):
    assert resolve(get(path), mtls=False) is Route.NOT_FOUND
    assert resolve(get(path), mtls=True) is Route.NOT_FOUND


def test_only_the_root_is_the_page():
    assert resolve(get("/"), mtls=False) is Route.PAGE
    # Not a prefix match. `/index.html`, `/portal`, `/favicon.ico` and everything else a
    # probe or a crawler might try are unknown, which is what keeps the set of paths that
    # answer 200 to exactly the ones named here.
    for path in ["/index.html", "/portal", "/favicon.ico", "/.well-known/x", "//"]:
        assert resolve(get(path), mtls=False) is Route.NOT_FOUND


def test_the_downloads_have_the_two_names_they_need():
    assert resolve(get("/loom-server-ca.pem"), mtls=False) is Route.ANCHOR_PEM
    assert resolve(get("/loom-server-ca.crt"), mtls=False) is Route.ANCHOR_CRT
    assert resolve(get("/fingerprint.txt"), mtls=False) is Route.FINGERPRINT


def test_the_logo_is_its_own_route():
    assert resolve(get("/logo.png"), mtls=False) is Route.LOGO


def test_issuance_does_not_exist_without_mutual_tls():
    """Not a 403: an endpoint that refuses still says there are certificates here."""
    post = Request(method="POST", path="/certificate")
    assert resolve(post, mtls=False) is Route.NOT_FOUND
    assert resolve(get("/certificate"), mtls=False) is Route.NOT_FOUND

    assert resolve(post, mtls=True) is Route.ISSUE
    assert resolve(get("/certificate"), mtls=True) is Route.ISSUE_RELOAD


def test_a_head_is_answered_like_a_get():
    """Some probes send HEAD, and an unanswered method is a 404 -- never a 200."""
    assert resolve(Request(method="HEAD", path="/"), mtls=False) is Route.PAGE
    assert (
        resolve(Request(method="HEAD", path="/generate_204"), mtls=False)
        is Route.NOT_FOUND
    )


def test_an_unexpected_method_is_not_found():
    for method in ["PUT", "DELETE", "PATCH", "OPTIONS"]:
        assert resolve(Request(method=method, path="/"), mtls=True) is Route.NOT_FOUND
        assert (
            resolve(Request(method=method, path="/certificate"), mtls=True)
            is Route.NOT_FOUND
        )
