"""Which answer a request gets, decided from the method and the path alone.

Pure, and separate from `portal.py`, for one reason: the single thing this feature could
break and nobody would notice is captive-portal detection. Every operating system
decides whether a network reaches the internet by fetching a URL whose answer it already
knows -- `/generate_204`, `/hotspot-detect.html`, `/ncsi.txt` -- and treats a `204` or
the expected body as "there is internet here". A page served at one of those paths with
status 200 is read as success by some probes and as a portal by others, and the
difference between "Sign in to network" and a phone quietly falling back to mobile data
is invisible from a browser.

So no path this module has never heard of resolves to the page. Unknown is `NOT_FOUND`,
and `tests/test_routes.py` holds the table of real probe paths that must never come back
as the page.

A probe now *does* reach this process, which it did not use to -- nginx answered the
whole catch-all with a static 302. What changed is that the answer became conditional:
the redirect is still the default, and the success below is the exception, granted to a
client that has pressed the button at the bottom of the page. The catch-all's `location
/` is still a static 302, so only the paths in `PROBE_ANSWERS` are proxied here at all,
and `test_routes.py` now guards both directions -- that each of them resolves to
`Route.PROBE`, and that none of them is ever the page.
"""

from dataclasses import dataclass
from enum import StrEnum

from loom_portal.http import Request

# The page itself, and the only path that renders it.
PAGE_PATH = "/"
LOGO_PATH = "/logo.png"
# Two names for one file. `.pem` is what a Linux or curl user wants; `.crt` is served as
# `application/x-x509-ca-cert`, which is the MIME type that makes iOS Safari and Android
# offer to *install* a certificate rather than print it as text.
ANCHOR_PEM_PATH = "/loom-server-ca.pem"
ANCHOR_CRT_PATH = "/loom-server-ca.crt"
FINGERPRINT_PATH = "/fingerprint.txt"
ISSUE_PATH = "/certificate"
# The button at the bottom of the page: "I am done here, stop the warning".
FINISH_PATH = "/done"


@dataclass(frozen=True)
class ProbeAnswer:
    """What a probe path answers a client that has finished with the page.

    Byte-exact, and that is the whole of it. Windows compares the body of
    `connecttest.txt` against `Microsoft Connect Test` character for character, Firefox
    compares `canonical.html` against its own `captivedetect.canonicalContent` default,
    and Apple's agent looks for `<TITLE>Success</TITLE>`. A trailing newline in the
    wrong place is the difference between a network marked good and one marked limited,
    and nothing in this repository but the test beside this table can see it.
    """

    status: int
    content_type: str = ""
    body: str = ""


_EMPTY = ProbeAnswer(status=204)
_APPLE = ProbeAnswer(
    status=200,
    content_type="text/html",
    body="<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>\n",
)
# Two different strings, and the distinction is not decorative: the modern endpoint is
# `www.msftconnecttest.com/connecttest.txt` and the legacy one is
# `www.msftncsi.com/ncsi.txt`, and each is compared against its own constant. Neither
# carries a trailing newline.
_CONNECT_TEST = ProbeAnswer(
    status=200, content_type="text/plain", body="Microsoft Connect Test"
)
_NCSI = ProbeAnswer(status=200, content_type="text/plain", body="Microsoft NCSI")
_FIREFOX_TEXT = ProbeAnswer(status=200, content_type="text/plain", body="success\n")
# The one absolute URL this package serves that is not under `.loom`, and it is exempt
# from the island rule `page.py` follows for a reason that holds: Firefox compares this
# document byte for byte and never renders it when it matches, so the meta-refresh is
# inert in exactly the case this answer is given. Pointing it somewhere local would make
# the comparison fail and open the portal tab -- which is the behaviour this route
# exists to stop.
_FIREFOX_HTML = ProbeAnswer(
    status=200,
    content_type="text/html",
    body='<meta http-equiv="refresh" '
    'content="0;url=https://support.mozilla.org/kb/captive-portal"/>',
)
_GNOME = ProbeAnswer(
    status=200, content_type="text/plain", body="NetworkManager is online\n"
)

# The probe contract, as one table.
#
# Deliberately the same list `tests/test_routes.py` has guarded since this module was
# written. That test used to assert every one of these resolves to `NOT_FOUND`; it now
# asserts that every one resolves to `PROBE` and that none is ever the page.
#
# portal.nix proxies exactly these paths to this process and nothing else, so the list
# is also a contract with the nginx configuration -- `loom_tests/appliance/portal.py`
# counts them in the rendered file.
PROBE_ANSWERS = {
    # Android and the AOSP family, Samsung, and the GNOME/KDE/Ubuntu desktops.
    "/generate_204": _EMPTY,
    "/gen_204": _EMPTY,
    "/generate204": _EMPTY,
    "/redirect": _EMPTY,
    "/check_network_status.txt": _GNOME,
    # Apple, both the modern path and the older one still in the fallback list.
    "/hotspot-detect.html": _APPLE,
    "/library/test/success.html": _APPLE,
    # Windows NCSI, modern and legacy.
    "/connecttest.txt": _CONNECT_TEST,
    "/ncsi.txt": _NCSI,
    # Firefox.
    "/success.txt": _FIREFOX_TEXT,
    "/canonical.html": _FIREFOX_HTML,
}


class Route(StrEnum):
    PAGE = "page"
    LOGO = "logo"
    ANCHOR_PEM = "anchor-pem"
    ANCHOR_CRT = "anchor-crt"
    FINGERPRINT = "fingerprint"
    ISSUE = "issue"
    # A GET on the issuance path, which is a reload after a download. Answered with a
    # redirect to the page rather than by issuing a second certificate.
    ISSUE_RELOAD = "issue-reload"
    # A connectivity probe. One member rather than one per vendor: this module decides
    # what a path *is*, and `portal.py` decides whether the client asking has earned the
    # success answer or gets the redirect every other client gets. Keeping that decision
    # out of here is what keeps `resolve` a pure function of the method and the path,
    # which is this module's reason to exist.
    PROBE = "probe"
    # The button at the bottom of the page, and a reload of it.
    FINISH = "finish"
    FINISH_RELOAD = "finish-reload"
    NOT_FOUND = "not-found"


# Every path that may answer with anything but a 404 -- the issuance one excepted, since
# it depends on what this image is. A table rather than a chain of comparisons, because
# "which paths exist at all" is the security property this module is for and it should be
# one readable list.
READABLE = {
    PAGE_PATH: Route.PAGE,
    LOGO_PATH: Route.LOGO,
    ANCHOR_PEM_PATH: Route.ANCHOR_PEM,
    ANCHOR_CRT_PATH: Route.ANCHOR_CRT,
    FINGERPRINT_PATH: Route.FINGERPRINT,
}


def resolve(request: Request, mtls: bool) -> Route:
    """The route, or `NOT_FOUND`.

    `mtls` is what decides whether the issuance path exists at all. On a box that
    requires no client certificate it resolves to `NOT_FOUND` rather than to a route
    that refuses: an endpoint that answers 403 tells a prober that this box has
    certificates to hand out, and this one has not.
    """
    readable = request.method in ("GET", "HEAD")

    if request.path == ISSUE_PATH:
        # Not reachable at all on a box that requires no client certificate -- see the
        # docstring. `mtls` gates the path's existence, not its answer.
        if not mtls:
            return Route.NOT_FOUND
        return _posted(request, readable, Route.ISSUE, Route.ISSUE_RELOAD)

    if request.path == FINISH_PATH:
        # On every image, unlike issuance: telling a device to stop asking about this
        # network has nothing to do with whether the box hands out certificates.
        return _posted(request, readable, Route.FINISH, Route.FINISH_RELOAD)

    if readable and request.path in PROBE_ANSWERS:
        return Route.PROBE

    return READABLE.get(request.path, Route.NOT_FOUND) if readable else Route.NOT_FOUND


def _posted(request: Request, readable: bool, acted: Route, reloaded: Route) -> Route:
    """The shape both of this module's two actions have.

    A POST does the thing; a GET or HEAD is somebody's reload, prefetch, hovered link or
    restored tab and must do nothing. That distinction is load-bearing in both cases and
    for different reasons -- a second certificate issued for nobody, and a sign-in sheet
    closed while its owner was still reading the page.
    """
    if request.method == "POST":
        return acted
    return reloaded if readable else Route.NOT_FOUND
