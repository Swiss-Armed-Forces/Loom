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

So: no path this router has never heard of resolves to the page, and no probe path ever
does either. What changed is which non-page answer they get. The nginx catch-all used to
answer every probe with a static 302 and these paths were `NOT_FOUND` here; the listed
ones are now proxied to this process so a client that has pressed the button on the page
can be told what its vendor wants to hear. The redirect is still the default, so this
module resolves them all to one route and `portal.py` decides which of the two answers
the client asking has earned.
"""

import pytest

from loom_portal.http import Request
from loom_portal.routes import PROBE_ANSWERS, READABLE, Route, resolve

# The paths the intercepted probe hostnames are actually fetched with, plus the variants
# that have appeared across OS releases. None of them may be the page.
#
# The same list as `routes.PROBE_ANSWERS`, restated rather than imported: a test that
# took the table from the module it is checking would agree with whatever the table
# said, which is the one thing this file exists not to do. `test_every_probe_path_has_an
# _answer` is what keeps the two in step -- and did, on its first run.
PROBE_PATHS = [
    "/generate_204",  # Android, connectivitycheck.gstatic.com
    "/gen_204",  # Android, older
    "/generate204",  # Samsung and Xiaomi, which drop the underscore
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
    for mtls in (False, True):
        resolved = resolve(get(path), mtls=mtls)
        assert resolved is Route.PROBE
        assert resolved is not Route.PAGE


def test_every_probe_path_has_an_answer():
    """The two lists are the same list.

    A path in `PROBE_ANSWERS` that is not here is a vendor nobody wrote a case for; one
    here that is not there resolves to `PROBE` and then finds no answer, which
    `portal.py` turns into the redirect -- correct, and silently never a success.
    """
    assert set(PROBE_ANSWERS) == set(PROBE_PATHS)


def test_no_path_is_both_a_probe_and_a_page():
    """`/` is the page and must never acquire a probe's answer, in either direction."""
    assert set(PROBE_ANSWERS) & set(READABLE) == set()


def test_the_vendor_bodies_are_byte_exact():
    """The highest-value assertion in this package, and the least obvious.

    Windows compares `connecttest.txt` against `Microsoft Connect Test` character for
    character and Firefox compares `success.txt` against `success\n`; a trailing newline
    in the wrong place is the difference between a network marked good and one marked
    limited. Nothing else in this repository can see that -- not the browser, not curl,
    not the VM test, which reads the same constants this file does unless they are
    written out here as literals.
    """
    assert PROBE_ANSWERS["/generate_204"].status == 204
    assert PROBE_ANSWERS["/generate_204"].body == ""
    assert PROBE_ANSWERS["/connecttest.txt"].body == "Microsoft Connect Test"
    assert PROBE_ANSWERS["/ncsi.txt"].body == "Microsoft NCSI"
    assert PROBE_ANSWERS["/success.txt"].body == "success\n"
    assert "<TITLE>Success</TITLE>" in PROBE_ANSWERS["/hotspot-detect.html"].body


def test_the_finish_route_is_a_post_on_every_image():
    """Unlike issuance, which only exists on a mutual TLS box.

    POST and not GET is the load-bearing half: a prefetch, a reload or a restored tab
    would otherwise close somebody's sign-in sheet while they were still reading.
    """
    for mtls in (False, True):
        assert resolve(Request(method="POST", path="/done"), mtls=mtls) is Route.FINISH
        assert resolve(get("/done"), mtls=mtls) is Route.FINISH_RELOAD
        assert (
            resolve(Request(method="PUT", path="/done"), mtls=mtls) is Route.NOT_FOUND
        )


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
        resolve(Request(method="HEAD", path="/generate_204"), mtls=False) is Route.PROBE
    )
    assert (
        resolve(Request(method="HEAD", path="/nothing-here"), mtls=False)
        is Route.NOT_FOUND
    )


def test_an_unexpected_method_is_not_found():
    for method in ["PUT", "DELETE", "PATCH", "OPTIONS"]:
        assert resolve(Request(method=method, path="/"), mtls=True) is Route.NOT_FOUND
        assert (
            resolve(Request(method=method, path="/certificate"), mtls=True)
            is Route.NOT_FOUND
        )
