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
and nginx's catch-all server block answers the probes with a 302 before anything reaches
this process at all (portal.nix). `tests/test_routes.py` holds the table of real probe
paths that must never come back as 200.
"""

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
        if not mtls:
            return Route.NOT_FOUND
        if request.method == "POST":
            return Route.ISSUE
        return Route.ISSUE_RELOAD if readable else Route.NOT_FOUND

    return READABLE.get(request.path, Route.NOT_FOUND) if readable else Route.NOT_FOUND
