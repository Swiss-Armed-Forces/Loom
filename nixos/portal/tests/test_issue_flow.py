"""Issuance, through the real `Portal` with the spool substituted.

Built with `build_portal` rather than by hand, so the wiring under test is the wiring
the service runs -- a seam added to `Portal` fails here rather than quietly going
untested.

The assertion worth the most is the negative one: a request that did not present today's
password creates no spool entry at all. Everything else about the privilege split -- the
unprivileged user, the missing kubeconfig, the `IPAddressDeny` -- is asserted at
evaluation time in `nixos/tests/appliance-units.nix`. This is the half that says the
unprivileged half never even asks.
"""

from doubles_portal import (
    P12_BYTES,
    PASSWORD,
    FakeClock,
    FakeSpool,
    pending_tokens,
    settings_for,
    write_anchor,
    write_passwords,
)

from loom_portal.__main__ import build_portal
from loom_portal.http import Header, Request
from loom_portal.settings import PortalLimits
from loom_portal.spool import BundleFormat, IssuanceOutcome, IssuanceState

SECURE = [Header("X-Loom-Secure", "1")]


def portal_for(tmp_path, spool=None, mtls=True, limits=None, placeholder=""):
    settings = settings_for(
        tmp_path,
        mtls=mtls,
        secure_url="https://portal.loom/",
        limits=limits,
        tls_placeholder_path=placeholder,
    )
    write_passwords(settings)
    write_anchor(settings)
    return (
        build_portal(settings, clock=FakeClock(), spool=spool or FakeSpool()),
        settings,
    )


def post(
    password: str, label: str = "", fmt: str = "p12", secure: bool = True
) -> Request:
    body = f"password={password}&label={label}&format={fmt}".encode()
    return Request(
        method="POST",
        path="/certificate",
        body=body,
        headers=SECURE if secure else [Header("X-Loom-Secure", "0")],
    )


def header(response, name: str) -> str:
    for entry in response.headers:
        if entry.name.lower() == name.lower():
            return entry.value
    return ""


def test_the_right_password_gets_a_certificate(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD, label="alices-laptop"))

    assert response.status == 200
    assert response.body == P12_BYTES
    assert header(response, "Content-Type") == "application/x-pkcs12"
    assert "attachment" in header(response, "Content-Disposition")
    assert "visitor-0123abcd.p12" in header(response, "Content-Disposition")
    # Never cached: it is a private key.
    assert header(response, "Cache-Control") == "no-store"
    assert spool.issued == [("alices-laptop", BundleFormat.P12)]


def test_the_zip_is_asked_for_by_the_second_button(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    portal.handle(post(PASSWORD, fmt="zip"))
    assert spool.issued[0].want is BundleFormat.ZIP


def test_a_wrong_password_asks_the_box_for_nothing(tmp_path):
    spool = FakeSpool()
    portal, settings = portal_for(tmp_path, spool)

    response = portal.handle(post("not-todays-password"))

    assert response.status == 403
    assert not spool.issued
    assert not pending_tokens(settings)
    assert b"not today" in response.body


def test_an_empty_password_asks_the_box_for_nothing_either(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    assert portal.handle(post("")).status == 403
    assert not spool.issued


def test_a_plaintext_connection_is_refused_before_the_password_is_even_read(tmp_path):
    """The page hides the form over http; this is the other half of that."""
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD, secure=False))

    assert response.status == 403
    assert not spool.issued
    assert b"Not over this connection" in response.body


def test_a_bad_label_is_refused_without_spending_an_attempt(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD, label="../../etc/passwd"))

    assert response.status == 400
    assert not spool.issued
    # And the label is not reflected into the page unescaped.
    assert b"../../etc/passwd" not in response.body


def test_too_many_attempts_are_throttled_with_a_retry_after(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(
        tmp_path,
        spool,
        limits=PortalLimits(
            attempts=3, attempt_window_s=60.0, wrong_password_delay_s=0.0
        ),
    )

    for _ in range(3):
        portal.handle(post("wrong"))

    response = portal.handle(post(PASSWORD))
    assert response.status == 429
    assert int(header(response, "Retry-After")) >= 1
    assert not spool.issued


def test_a_cluster_that_is_not_up_yet_is_a_sentence_rather_than_an_error(tmp_path):
    spool = FakeSpool(IssuanceOutcome(state=IssuanceState.CLUSTER_NOT_READY))
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD))

    assert response.status == 503
    assert b"Loom is still starting" in response.body


def test_a_busy_box_says_when_to_come_back(tmp_path):
    spool = FakeSpool(IssuanceOutcome(state=IssuanceState.BUSY))
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD))
    assert response.status == 503
    assert header(response, "Retry-After") == "10"


def test_a_timeout_names_the_journal_unit_that_explains_it(tmp_path):
    spool = FakeSpool(IssuanceOutcome(state=IssuanceState.TIMED_OUT))
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(post(PASSWORD))
    assert response.status == 504
    assert b"loom-portal-issue" in response.body


def test_a_box_without_mutual_tls_has_no_such_endpoint(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool, mtls=False)

    assert portal.handle(post(PASSWORD)).status == 404
    assert not spool.issued


def test_reloading_after_a_download_does_not_issue_a_second_one(tmp_path):
    spool = FakeSpool()
    portal, _ = portal_for(tmp_path, spool)

    response = portal.handle(Request(method="GET", path="/certificate", headers=SECURE))

    assert response.status == 303
    assert header(response, "Location") == "/"
    assert not spool.issued


def test_the_anchor_is_offered_under_both_names(tmp_path):
    portal, _ = portal_for(tmp_path)

    crt = portal.handle(Request(method="GET", path="/loom-server-ca.crt"))
    pem = portal.handle(Request(method="GET", path="/loom-server-ca.pem"))

    assert crt.status == 200 and pem.status == 200
    assert crt.body == pem.body
    # The MIME type is the whole reason the second name exists.
    assert header(crt, "Content-Type") == "application/x-x509-ca-cert"
    assert header(pem, "Content-Type") == "application/x-pem-file"


def test_the_anchor_is_a_503_before_the_cluster_has_published_one(tmp_path):
    settings = settings_for(tmp_path, mtls=False)
    write_passwords(settings)
    portal = build_portal(settings, clock=FakeClock(), spool=FakeSpool())

    response = portal.handle(Request(method="GET", path="/loom-server-ca.pem"))
    assert response.status == 503
    assert b"Not available yet" in response.body


def test_the_form_is_on_the_page_the_tls_listener_serves(tmp_path):
    """The gap between `render` knowing about the connection and `handle` telling it.

    `test_page.py` asserts that the form appears when the model says the connection is
    encrypted. This asserts the other half: that a `GET /` arriving on the TLS listener
    produces such a model. Without it the secure page renders its own "reopen securely"
    link, and a visitor follows it back to the page they are already on, forever.
    """
    portal, _ = portal_for(tmp_path)

    secure = portal.handle(Request(method="GET", path="/", headers=SECURE))
    plain = portal.handle(Request(method="GET", path="/"))

    assert b'<form method="post" action="/certificate">' in secure.body
    # The certificate form specifically -- the page's own "stop the warning" button is
    # a form too, and is offered on both listeners.
    assert b'action="/certificate"' not in plain.body
    assert b"https://portal.loom/#identity" in plain.body


def test_no_certificate_is_handed_out_over_the_placeholder_listener(tmp_path):
    """443 comes up long before the cluster does, on a pair nothing can verify.

    `loom-portal-tls-placeholder` writes a one-day self-signed `CN=portal.loom`
    certificate so that nginx starts at all, and on a first boot that is in force for
    hours -- exactly the period this page exists to cover. `X-Loom-Secure` records which
    listener answered, not which certificate it answered with, so the marker that unit
    leaves behind is what the form is really gated on.
    """
    marker = tmp_path / "placeholder"
    marker.write_text("")
    portal, _ = portal_for(tmp_path, placeholder=str(marker))

    refused = portal.handle(post(PASSWORD))
    assert refused.status == 403
    assert "Not over this connection" in refused.body.decode()

    # And the page offers the form the moment the real certificate is published.
    marker.unlink()
    assert portal.handle(post(PASSWORD)).status == 200
