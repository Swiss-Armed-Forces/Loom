"""The whole application, as a function of a request.

`Portal.handle` opens no socket, reads no environment and starts no process. Everything
that touches the outside world is one of four objects it was constructed with -- the
anchor file, the password gate, the spool and the validated-client set -- so the suite
drives the real application end to end without binding a port or waiting for anything.
Each of those holds the clock it needs; this class never asks the time itself.

What this service is allowed to do is deliberately small, and the systemd unit in
portal.nix enforces it: it runs as its own user, has no kubeconfig, has `IPAddressDeny`
set to everything but loopback, and can write to exactly three directories. It shells
out to nothing. The expensive and privileged half of issuing a certificate happens in a
root unit on the other side of a spool directory -- see `spool.py`.
"""

import logging
import os

from loom_portal.anchor import AnchorFile
from loom_portal.guides import GuideContext, anchor_guides, identity_guides
from loom_portal.http import (
    Header,
    Request,
    Response,
    attachment,
    html,
    no_content,
    no_store,
    parse_form,
    redirect,
    text,
)
from loom_portal.page import (
    Notice,
    NoticeKind,
    PageConditions,
    PageGuides,
    PageModel,
    render,
)
from loom_portal.password import PasswordGate
from loom_portal.routes import (
    ANCHOR_PEM_PATH,
    PAGE_PATH,
    PROBE_ANSWERS,
    Route,
    resolve,
)
from loom_portal.settings import PortalSettings
from loom_portal.spool import BundleFormat, IssuanceState, Spool, validate_label
from loom_portal.validated import ValidatedClients

logger = logging.getLogger(__name__)

# nginx sets this on both page vhosts: `1` on the TLS one and `0` on the plaintext one.
# Set on both rather than only where it is true, so a header a client invented cannot
# survive -- nginx replaces whatever arrived.
SECURE_HEADER = "X-Loom-Secure"

# The only fact about a visitor this service is ever told, and the one that decides
# whether their next connectivity probe is answered with a success or with the redirect
# everybody else gets. nginx sets it on every proxied location on every listener, for
# the reason the note on `SECURE_HEADER` gives.
#
# Empty when something dialled the loopback port directly, and an empty client is never
# a validated one -- see `ValidatedClients.has`.
CLIENT_HEADER = "X-Loom-Client"

# What `_finish` redirects to, so the page can say the button worked.
FINISHED_QUERY = "finished=1"

# The one answer that may be cached. It is the Loom mark and nothing else, and a phone
# that reloads the page three times should not fetch it three times.
LOGO_CACHE_SECONDS = 300

NOT_FOUND_BODY = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    "<title>Not found</title></head><body>"
    '<p>Nothing here. <a href="/">The appliance page</a>.</p>'
    "</body></html>"
)


class Portal:
    """The router, and the four seams everything below it goes through."""

    def __init__(
        self,
        settings: PortalSettings,
        anchor: AnchorFile,
        gate: PasswordGate,
        spool: Spool,
        validated: ValidatedClients,
    ):
        self.settings = settings
        self.anchor = anchor
        self.gate = gate
        self.spool = spool
        self.validated = validated

    # -- routing ------------------------------------------------------------------

    def handle(self, request: Request) -> Response:
        route = resolve(request, self.settings.mtls)

        if route is Route.PROBE:
            return self._probe(request)
        if route is Route.FINISH:
            return self._finish(request)
        if route is Route.FINISH_RELOAD:
            # A reload, a prefetch, or somebody's restored tab. Answered with the page
            # and nothing else -- see `resolve`, which is where the reason lives.
            return redirect(PAGE_PATH)
        if route is Route.ISSUE:
            return self._issue(request)
        if route is Route.ISSUE_RELOAD:
            # A reload after a download, or a bookmarked URL. Answered with the page
            # rather than by issuing a second certificate for nobody.
            return redirect(PAGE_PATH)
        return self._read(request, route)

    # -- telling an operating system what it wants to hear --------------------------

    def _probe(self, request: Request) -> Response:
        """A connectivity probe.

        The redirect is the default and the success is the exception, which is the
        inverse of how the feature reads. A client that has not pressed the button gets
        byte-for-byte what nginx's catch-all would have given it, so the only thing this
        route can get wrong in the dangerous direction -- answering too many clients
        with a success -- is one condition on one line, and `tests/test_probe_flow.py`
        drives both sides of it.
        """
        answer = PROBE_ANSWERS.get(request.path)
        if answer is None or not self.validated.has(_client_of(request)):
            return redirect(self.settings.urls.portal_redirect, status=302)
        if answer.status == 204:
            return no_content()
        return Response(
            status=answer.status,
            headers=no_store([Header("Content-Type", answer.content_type)]),
            body=answer.body.encode("utf-8"),
        )

    def _finish(self, request: Request) -> Response:
        """The button at the bottom of the page.

        Logged without the address. `server.py` replaced `address_string` with a dash
        for the same reason, and a line naming who stopped asking would put back exactly
        what `validated.py` goes to the trouble of not storing.
        """
        if not self.validated.mark(_client_of(request)):
            # The page is still there and the button simply did not take, so the
            # visitor gets the page back with the button still on it -- which is
            # honest. A warning, because the only way here is a directory this service
            # cannot write.
            logger.warning("Could not mark a client as finished with the page.")
            return redirect(PAGE_PATH)
        logger.info("A client asked to stop being asked about this network.")
        return redirect(f"{PAGE_PATH}?{FINISHED_QUERY}")

    def _secure_enough(self, request: Request) -> bool:
        """Whether this connection may carry an unencrypted private key.

        `X-Loom-Secure` records which *listener* answered, not which certificate is in
        force -- and 443 comes up on `loom-portal-tls-placeholder`'s one-day self-signed
        `CN=portal.loom` pair, which nothing can verify. On a first boot that is the
        state for hours, which is exactly the period this page exists to cover. So the
        marker that unit leaves behind is consulted too, and the form is only offered
        once `loom-portal-certificate` has published the cluster's own certificate --
        the one the visitor was told to trust.
        """
        if not _is_secure(request):
            return False
        return not self.settings.tls_is_placeholder

    def _read(self, request: Request, route: Route) -> Response:
        """Everything that only reads: the page and the three downloads.

        The request is threaded through for one reason, and it is the whole mutual TLS
        flow: the page only offers the certificate form when it is being served over an
        encrypted connection, so a `GET /` that did not carry that answer would render
        the "reopen securely" link on the secure listener as well -- a loop with no way
        out of it.
        """
        if route is Route.PAGE:
            validated = self.validated.has(_client_of(request))
            return html(
                render(
                    self._model(
                        self._secure_enough(request),
                        notice=_finished_notice(request, validated),
                        validated=validated,
                    )
                )
            )
        if route is Route.LOGO:
            return self._logo()
        if route in (Route.ANCHOR_PEM, Route.ANCHOR_CRT):
            return self._anchor_download(request, route)
        if route is Route.FINGERPRINT:
            return self._fingerprint()
        return html(NOT_FOUND_BODY, status=404)

    # -- the page -----------------------------------------------------------------

    def _model(
        self,
        secure: bool = False,
        notice: Notice | None = None,
        validated: bool = False,
    ) -> PageModel:
        context = GuideContext(
            anchor_filename=os.path.basename(ANCHOR_PEM_PATH),
            frontend_host=_host_of(self.settings.urls.frontend),
        )
        return PageModel(
            brand=self.settings.brand,
            urls=self.settings.urls,
            conditions=PageConditions(
                secure=secure, mtls=self.settings.mtls, validated=validated
            ),
            anchor=self.anchor.read(),
            notice=notice,
            guides=PageGuides(
                anchor=anchor_guides(context), identity=identity_guides(context)
            ),
        )

    def _page(
        self,
        request: Request,
        notice: Notice | None,
        status: int,
        extra: list[Header] | None = None,
    ) -> Response:
        response = html(
            render(
                self._model(
                    self._secure_enough(request),
                    notice,
                    validated=self.validated.has(_client_of(request)),
                )
            ),
            status=status,
        )
        if extra:
            return Response(
                status=response.status,
                headers=[*response.headers, *extra],
                body=response.body,
            )
        return response

    # -- the certificate everybody needs -------------------------------------------

    def _anchor_download(self, request: Request, route: Route) -> Response:
        status = self.anchor.read()
        if not status.available:
            # 503 rather than 404: the file is missing because Loom has not come up, not
            # because this box has nothing to offer, and a visitor who reloads in ten
            # minutes gets it.
            return html(
                render(
                    self._model(
                        self._secure_enough(request),
                        validated=self.validated.has(_client_of(request)),
                    )
                ),
                status=503,
            )

        if route is Route.ANCHOR_CRT:
            # The MIME type is the whole reason this second name exists: iOS Safari and
            # Android offer to *install* an `application/x-x509-ca-cert` and display an
            # `application/x-pem-file` as text.
            return attachment(
                status.pem, "loom-server-ca.crt", "application/x-x509-ca-cert"
            )
        return attachment(status.pem, "loom-server-ca.pem", "application/x-pem-file")

    def _fingerprint(self) -> Response:
        status = self.anchor.read()
        if not status.fingerprint:
            return text("", status=503)
        return text(status.fingerprint + "\n")

    # -- the certificate only an mTLS box hands out ---------------------------------

    def _issue(self, request: Request) -> Response:
        if not self._secure_enough(request):
            # The page does not show the form over plaintext, and this is the other half
            # of that: a PKCS#12 holds an unencrypted private key, and the appliance
            # segment is a wire that -- on a --wifi box -- is everybody in radio range.
            # "Encrypted" also has to mean "by a certificate somebody can verify" --
            # see `_secure_enough`.
            return self._page(
                request,
                Notice(
                    NoticeKind.WARN,
                    "Not over this connection.",
                    "A certificate is only handed out over an encrypted connection.",
                ),
                status=403,
            )

        form = parse_form(request.body)

        label = validate_label(form.get("label"))
        if not label.ok:
            return self._page(
                request,
                Notice(NoticeKind.BAD, "That name will not do.", label.reason),
                status=400,
            )

        check = self.gate.check(form.get("password"))
        if check.throttled:
            return self._page(
                request,
                Notice(
                    NoticeKind.WARN,
                    "Too many attempts.",
                    "Wait a minute and try again. The password is on the screen "
                    "attached to the box.",
                ),
                status=429,
                extra=[Header("Retry-After", str(max(1, int(check.retry_after_s))))],
            )
        if not check.accepted:
            return self._page(
                request,
                Notice(
                    NoticeKind.BAD,
                    "That password is not today's.",
                    "It is on the screen attached to the box, and it changes every day.",
                ),
                status=403,
            )

        want = (
            BundleFormat.ZIP
            if form.get("format") == BundleFormat.ZIP.value
            else BundleFormat.P12
        )
        outcome = self.spool.issue(label.label, want)

        if outcome.state is IssuanceState.DELIVERED:
            logger.info("Issued a client certificate as %s.", outcome.filename)
            return attachment(outcome.bundle, outcome.filename, outcome.content_type)

        return self._refusal(request, outcome.state)

    def _refusal(self, request: Request, state: IssuanceState) -> Response:
        if state is IssuanceState.CLUSTER_NOT_READY:
            return self._page(
                request,
                Notice(
                    NoticeKind.WARN,
                    "Loom is still starting.",
                    "This box cannot issue a certificate until the cluster is up. "
                    "On a first boot that can take a while.",
                ),
                status=503,
            )
        if state is IssuanceState.BUSY:
            return self._page(
                request,
                Notice(
                    NoticeKind.WARN,
                    "The box is busy.",
                    "It is making a certificate for somebody else. Try again in a "
                    "moment.",
                ),
                status=503,
                extra=[Header("Retry-After", "10")],
            )
        if state is IssuanceState.TIMED_OUT:
            return self._page(
                request,
                Notice(
                    NoticeKind.WARN,
                    "That took too long.",
                    "Nothing came back in time. Try again; if it keeps happening, the "
                    "operator can see why with: journalctl -u loom-portal-issue",
                ),
                status=504,
            )
        return self._page(
            request,
            Notice(
                NoticeKind.BAD,
                "The box could not issue a certificate.",
                "The operator can see why with: journalctl -u loom-portal-issue",
            ),
            status=500,
        )

    # -- the mark ------------------------------------------------------------------

    def _logo(self) -> Response:
        try:
            with open(self.settings.brand.logo_path, "rb") as handle:
                payload = handle.read()
        except OSError as error:
            # The page carries an empty `alt`, so a missing mark costs the look and
            # nothing else. branding.nix has already refused to build an image whose
            # logo is an unmaterialised git-lfs pointer, so this is close to unreachable.
            logger.warning("Could not read the logo: %s", error)
            return Response(status=404)
        return Response(
            status=200,
            headers=[
                Header("Content-Type", "image/png"),
                Header("Cache-Control", f"max-age={LOGO_CACHE_SECONDS}"),
                Header("Content-Length", str(len(payload))),
            ],
            body=payload,
        )


def _is_secure(request: Request) -> bool:
    return request.header(SECURE_HEADER) == "1"


def _client_of(request: Request) -> str:
    """Which client this is, as nginx saw it.

    Empty when nothing set the header, which is every request that reached the loopback
    port without going through nginx. `ValidatedClients` treats that as nobody.
    """
    return request.header(CLIENT_HEADER)


def _finished_notice(request: Request, validated: bool) -> Notice | None:
    """The "that worked" line, after the button.

    Both conditions, and the second is the one that matters: `/?finished=1` is a URL
    anybody can type, and a page that congratulated a visitor on something that did not
    happen would be worse than one that said nothing. The query only decides whether to
    mention it; `validated` decides whether it is true.
    """
    if FINISHED_QUERY not in request.query or not validated:
        return None
    return Notice(
        NoticeKind.GOOD,
        "This device has stopped asking.",
        "It will no longer warn you that this network has no internet. It still has "
        "none -- so everything that is not Loom will now fail quietly rather than "
        "loudly.",
    )


def _host_of(url: str) -> str:
    """The host out of one of the three URLs Nix computed.

    Hand-rolled rather than `urllib.parse`, because the only thing it is used for is
    naming a host in an instruction, and the inputs are two literals this box built
    itself.
    """
    stripped = url.split("://", 1)[-1]
    return stripped.split("/", 1)[0]
