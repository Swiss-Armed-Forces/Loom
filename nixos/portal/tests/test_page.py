"""The page, rendered.

`render` is pure, so everything here is an assertion about a string. Two of them are
worth more than the rest:

  * **The island property.** Every absolute URL in the document has to be under `.loom`,
    and there may be no `<script src=>` and no `<link>`. The appliance has no upstream, so
    a page that reaches for a CDN font does not degrade gracefully -- it hangs for the
    browser's connect timeout and then renders unstyled, on the first screen a visitor
    ever sees. A stylesheet moved into a file "for tidiness" is exactly the change this
    catches.
  * **The frontend link follows the build.** A `--require-client-cert` box serves no
    plain http at all, so `http://frontend.loom/` is a dead link there and `https://` is
    a dead link on every other image's portal webview. Nix computes it; this asserts the
    page prints what it was given rather than a literal.
"""

import re

from loom_portal.anchor import AnchorStatus
from loom_portal.guides import GuideContext, anchor_guides, identity_guides
from loom_portal.page import Notice, NoticeKind, PageGuides, PageModel, render
from loom_portal.settings import PortalUrls

FINGERPRINT = ":".join(["AB"] * 32)

# Every `scheme://host` in the document.
ABSOLUTE_URL = re.compile(r"(?:https?)://([A-Za-z0-9.\-]+)")


def model(
    *,
    mtls: bool = False,
    secure: bool = False,
    urls: PortalUrls | None = None,
    anchor: AnchorStatus | None = None,
    notice: Notice | None = None,
) -> PageModel:
    """A page model with the guides filled in, which is what the real one always has."""
    context = GuideContext()
    return PageModel(
        urls=urls or PortalUrls(),
        secure=secure,
        mtls=mtls,
        anchor=anchor
        or AnchorStatus(available=True, pem=b"x", fingerprint=FINGERPRINT),
        notice=notice,
        guides=PageGuides(
            anchor=anchor_guides(context), identity=identity_guides(context)
        ),
    )


def test_the_page_reaches_for_nothing_outside_the_box():
    markup = render(model(mtls=True, secure=True))

    for host in ABSOLUTE_URL.findall(markup):
        assert host.endswith(
            ".loom"
        ), f"the page links to {host}, which is not on the box"

    assert "<script" not in markup
    assert "<link" not in markup
    # A web font is the specific way this gets reintroduced, and it does not announce
    # itself as a link tag.
    assert "@import" not in markup
    assert "fonts.googleapis" not in markup


def test_the_only_image_is_served_by_this_process():
    markup = render(model())
    sources = re.findall(r'<img[^>]+src="([^"]+)"', markup)
    assert sources == ["/logo.png"]


def test_the_frontend_link_is_whatever_nix_computed():
    plain = render(model(urls=PortalUrls(frontend="http://frontend.loom/")))
    assert 'href="http://frontend.loom/"' in plain

    # The mutual TLS build, which serves no plain http at all.
    secured = render(
        model(
            mtls=True, secure=True, urls=PortalUrls(frontend="https://frontend.loom/")
        )
    )
    assert 'href="https://frontend.loom/"' in secured
    assert "http://frontend.loom/" not in secured


def test_the_identity_section_exists_only_on_a_mutual_tls_box():
    assert 'id="identity"' not in render(model(mtls=False))
    assert 'id="identity"' in render(
        model(mtls=True, secure=True, urls=PortalUrls(secure="https://portal.loom/"))
    )


def test_the_form_is_not_offered_over_a_plaintext_connection():
    """A PKCS#12 carries an unencrypted private key; the segment is a wire."""
    markup = render(
        model(mtls=True, secure=False, urls=PortalUrls(secure="https://portal.loom/"))
    )
    assert "<form" not in markup
    assert 'href="https://portal.loom/#identity"' in markup


def test_the_form_is_offered_once_the_connection_is_encrypted():
    markup = render(
        model(mtls=True, secure=True, urls=PortalUrls(secure="https://portal.loom/"))
    )
    assert '<form method="post" action="/certificate">' in markup
    assert 'name="password"' in markup
    assert 'value="p12"' in markup
    assert 'value="zip"' in markup


def test_a_box_whose_anchor_has_not_arrived_says_so_rather_than_offering_it():
    markup = render(model(anchor=AnchorStatus(available=False)))
    assert "Not available yet" in markup
    assert "/loom-server-ca.crt" not in markup


def test_the_fingerprint_is_shown_when_there_is_one():
    assert FINGERPRINT in render(model())
    bare = render(model(anchor=AnchorStatus(available=True, pem=b"x", fingerprint="")))
    assert "SHA-256" not in bare
    # The download is still offered: a fingerprint nobody can read is a reason to compare
    # it elsewhere, not a reason to withhold the certificate.
    assert "/loom-server-ca.crt" in bare


def test_a_notice_is_escaped():
    """The only user-supplied text that reaches the page is a rejected label."""
    markup = render(
        model(
            notice=Notice(
                NoticeKind.BAD, "That name will not do.", "<script>alert(1)</script>"
            )
        )
    )
    assert "<script>alert(1)</script>" not in markup
    assert "&lt;script&gt;" in markup


def test_the_mutual_tls_box_explains_why_loom_will_refuse_the_browser():
    """The failure it is explaining has no page of its own: Traefik refuses in the
    handshake, so a visitor who has not read this sees only a browser error."""
    markup = render(
        model(mtls=True, secure=True, urls=PortalUrls(secure="https://portal.loom/"))
    )
    assert "requires a client certificate" in markup
    assert "before any request is read" in markup
