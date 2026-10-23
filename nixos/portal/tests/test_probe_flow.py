"""Connectivity probes, through the real `Portal`.

Built with `build_portal` for the reason `test_issue_flow.py` gives: a seam added to
`Portal` fails here rather than quietly going untested.

`test_routes.py` says which paths are probes and what each vendor's body has to be. This
says who gets them -- which is the half that can be wrong in a way nobody notices,
because every failure mode here looks like a working portal from the one device the
person testing is holding.
"""

from doubles_portal import (
    PROBE_REDIRECT,
    FakeClock,
    FakeSpool,
    settings_for,
    write_anchor,
)

from loom_portal.__main__ import build_portal
from loom_portal.http import Header, Request
from loom_portal.settings import DEFAULT_VALIDATED_TTL_S

CLIENT = "10.13.37.137"
OTHER = "10.13.37.138"


def portal_for(tmp_path, clock=None):
    settings = settings_for(tmp_path)
    write_anchor(settings)
    return build_portal(settings, clock=clock or FakeClock(), spool=FakeSpool())


def probe(portal, path: str, client: str = CLIENT):
    headers = [Header("X-Loom-Client", client)] if client else []
    return portal.handle(Request(method="GET", path=path, headers=headers))


def finish(portal, client: str = CLIENT):
    headers = [Header("X-Loom-Client", client)] if client else []
    return portal.handle(Request(method="POST", path="/done", headers=headers))


def test_an_unvalidated_probe_gets_the_same_redirect_nginx_would_have_given(tmp_path):
    """The default, and the direction that is safe to get wrong.

    Byte-for-byte what the catch-all's static `return 302` answers, so a client cannot
    tell whether the page server was even up.
    """
    answer = probe(portal_for(tmp_path), "/generate_204")
    assert answer.status == 302
    assert Header("Location", PROBE_REDIRECT) in answer.headers


def test_a_finished_client_gets_the_vendor_answer(tmp_path):
    portal = portal_for(tmp_path)
    assert finish(portal).status == 303

    empty = probe(portal, "/generate_204")
    assert empty.status == 204
    assert empty.body == b""
    # RFC 9110 forbids the header on a 204, and this is the one response whose exact
    # framing something that is not a browser reads and acts on.
    assert all(header.name.lower() != "content-length" for header in empty.headers)

    assert b"<TITLE>Success</TITLE>" in probe(portal, "/hotspot-detect.html").body
    assert probe(portal, "/connecttest.txt").body == b"Microsoft Connect Test"
    assert probe(portal, "/ncsi.txt").body == b"Microsoft NCSI"
    assert probe(portal, "/success.txt").body == b"success\n"


def test_another_client_still_gets_the_redirect(tmp_path):
    """The per-client property, and the one a global flag would silently break."""
    portal = portal_for(tmp_path)
    finish(portal, CLIENT)

    assert probe(portal, "/generate_204", client=OTHER).status == 302


def test_a_probe_with_no_client_header_gets_the_redirect(tmp_path):
    """Nothing but something dialling the loopback port directly arrives this way, and
    the absence of the header must never read as "everybody"."""
    portal = portal_for(tmp_path)
    finish(portal, CLIENT)

    assert probe(portal, "/generate_204", client="").status == 302


def test_a_get_on_the_button_changes_nothing(tmp_path):
    """A prefetch, a reload or a restored tab must not close somebody's sign-in sheet
    while they are still reading the page."""
    portal = portal_for(tmp_path)

    reload_answer = portal.handle(
        Request(method="GET", path="/done", headers=[Header("X-Loom-Client", CLIENT)])
    )
    assert reload_answer.status == 303
    assert Header("Location", "/") in reload_answer.headers
    assert probe(portal, "/generate_204").status == 302


def test_the_answer_goes_back_to_the_redirect_when_the_marker_expires(tmp_path):
    clock = FakeClock()
    portal = portal_for(tmp_path, clock)
    finish(portal)
    assert probe(portal, "/generate_204").status == 204

    clock.current += DEFAULT_VALIDATED_TTL_S + 1
    assert probe(portal, "/generate_204").status == 302


def test_the_page_says_it_worked_only_when_it_did(tmp_path):
    """`/?finished=1` is a URL anybody can type, and a page that congratulated a visitor
    on something that did not happen would be worse than one saying nothing."""
    portal = portal_for(tmp_path)

    untouched = portal.handle(
        Request(
            method="GET",
            path="/",
            query="finished=1",
            headers=[Header("X-Loom-Client", CLIENT)],
        )
    )
    assert b"has stopped asking" not in untouched.body

    finish(portal)
    after = portal.handle(
        Request(
            method="GET",
            path="/",
            query="finished=1",
            headers=[Header("X-Loom-Client", CLIENT)],
        )
    )
    assert b"has stopped asking" in after.body


def test_the_page_drops_the_button_once_it_has_been_pressed(tmp_path):
    portal = portal_for(tmp_path)
    page = portal.handle(
        Request(method="GET", path="/", headers=[Header("X-Loom-Client", CLIENT)])
    )
    assert b'action="/done"' in page.body

    finish(portal)
    after = portal.handle(
        Request(method="GET", path="/", headers=[Header("X-Loom-Client", CLIENT)])
    )
    assert b'action="/done"' not in after.body
