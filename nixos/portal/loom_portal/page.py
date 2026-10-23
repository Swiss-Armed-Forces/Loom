"""The page itself.

A Python template rather than a static file built in Nix, for three reasons:

  * It is not static. It shows whether the box's certificate has been published yet, what
    its fingerprint is, whether this image requires a client certificate, and the result
    of the last attempt to get one.
  * `render` being a pure function of a `PageModel` is what lets `tests/test_page.py`
    assert the property below without building anything.
  * It is the shape `loom_ready.render` already uses for the console.

**The page is an island.** No `<script src=>`, no `<link>`, no web font, no image from
anywhere but this server. The appliance has no upstream and advertises no default route,
so a page that reaches for a CDN does not degrade -- it hangs for the browser's connect
timeout and then renders unstyled, on the one screen a visitor sees before they have any
idea what this box is. `tests/test_page.py` asserts that every absolute URL in the
rendered document is under `.loom`.

The look is the frontend's, taken from the same places `nixos/branding.nix` takes the
console palette from: `Frontend/src/app/theme.ts` for the amber and the greys,
`Frontend/src/main.css` for the font stack and the light/dark layer colours. As that file
says, nothing checks these against the frontend at build time -- the frontend is not in
this closure -- so a brand change is a change in two places.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from html import escape

from loom_portal.anchor import AnchorStatus
from loom_portal.guides import InstallGuide
from loom_portal.settings import PortalBrand, PortalUrls


class NoticeKind(StrEnum):
    GOOD = "good"
    WARN = "warn"
    BAD = "bad"


@dataclass(frozen=True)
class Notice:
    """A message about what just happened, shown above everything else."""

    kind: NoticeKind
    heading: str
    body: str = ""


@dataclass(frozen=True)
class PageGuides:
    """The two sets of per-platform instructions, kept apart because they install two
    different things and the page says so in those words."""

    anchor: list[InstallGuide] = field(default_factory=list)
    identity: list[InstallGuide] = field(default_factory=list)


@dataclass(frozen=True)
class PageConditions:
    """The three answers that decide what this page shows, as one value.

    Each is about a different thing -- the connection, the image, the client -- and
    grouping them is what keeps `PageModel` a short list of nouns rather than a pile of
    flags. Every section below reads at most one of them.
    """

    # Whether this request itself arrived over TLS. Decides whether the issuance form is
    # shown or replaced by a link that moves the visitor onto the secure listener first.
    secure: bool = False
    # Whether this image requires a client certificate, and so has one to hand out.
    mtls: bool = False
    # Whether this client has already pressed the button at the bottom of the page.
    # Decides whether that section offers the button or reports what it did.
    validated: bool = False


@dataclass(frozen=True)
class PageModel:
    """Everything `render` needs.

    No I/O happens below this type.     `brand` and `urls` are the service's own values,
    straight out of `settings.py`, so     there is no second place where the amber or
    the frontend URL could be decided.
    """

    brand: PortalBrand = field(default_factory=PortalBrand)
    urls: PortalUrls = field(default_factory=PortalUrls)
    conditions: PageConditions = field(default_factory=PageConditions)
    anchor: AnchorStatus = field(default_factory=lambda: AnchorStatus(available=False))
    notice: Notice | None = None
    guides: PageGuides = field(default_factory=PageGuides)


def render(model: PageModel) -> str:
    """The whole document."""
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Loom appliance</title>",
            f"<style>{_stylesheet(model.brand.accent)}</style>",
            "</head>",
            "<body>",
            '<main class="page">',
            _header(model),
            _notice(model.notice),
            _open_loom(model),
            _anchor_section(model),
            _identity_section(model),
            _finish_section(model),
            _footer(model),
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _header(model: PageModel) -> str:
    return (
        '<header class="mark">'
        '<img src="/logo.png" alt="" width="64" height="64">'
        "<div><h1>Loom appliance</h1>"
        f'<p class="tag">{escape(model.brand.tag)}</p></div>'
        "</header>"
    )


def _notice(notice: Notice | None) -> str:
    if notice is None:
        return ""
    body = f"<p>{escape(notice.body)}</p>" if notice.body else ""
    return (
        f'<div class="notice {escape(notice.kind.value)}">'
        f"<strong>{escape(notice.heading)}</strong>{body}</div>"
    )


def _open_loom(model: PageModel) -> str:
    """The primary action, and the only thing most visitors came for.

    First on the page and styled as the one button, because on an image that requires no
    client certificate this page is a detour: the visitor tapped "Sign in to network" and
    wants Loom. Everything below it is for the minority who want the warning to stop, or
    who are on the one image where a certificate is not optional.
    """
    if not model.conditions.mtls:
        aside = (
            "<p>The certificate below is optional. Loom works without it; installing it "
            "is what stops your browser warning about this box.</p>"
        )
    else:
        aside = (
            "<p>This box requires a client certificate. Until you have installed one "
            "from the second section below, your browser will be refused when it "
            "connects &mdash; with no page and no explanation, because the refusal "
            "happens "
            "before any request is read.</p>"
        )
    return (
        '<section class="act">'
        f'<a class="primary" href="{escape(model.urls.frontend)}">Open Loom</a>'
        f"{aside}</section>"
    )


def _anchor_section(model: PageModel) -> str:
    heading = "<h2>Trust this box&rsquo;s certificate</h2>"
    explain = (
        "<p>Loom serves <code>*.loom</code>, which is not a real top-level domain, so no "
        "public authority can ever issue a certificate for it. This box signed its own. "
        "Install it and the warning goes away; skip it and you can click through the "
        "warning instead.</p>"
    )

    if not model.anchor.available:
        return (
            f'<section id="certificate">{heading}{explain}'
            '<div class="notice warn"><strong>Not available yet.</strong>'
            "<p>Loom is still starting. This box publishes its certificate once the "
            "cluster is up, which on a first boot can take a while. Reload this page "
            "later.</p></div></section>"
        )

    fingerprint = ""
    if model.anchor.fingerprint:
        fingerprint = (
            '<p class="fp">SHA-256<br>'
            f"<code>{escape(model.anchor.fingerprint)}</code></p>"
            "<p>Compare it against the box&rsquo;s own console before you trust it. "
            "A fingerprint checked only against the page that served it proves "
            "nothing.</p>"
        )

    return (
        f'<section id="certificate">{heading}{explain}'
        '<p><a class="download" href="/loom-server-ca.crt">Download the certificate</a>'
        '<a class="plain" href="/loom-server-ca.pem">PEM, for curl and Linux</a></p>'
        f"{fingerprint}"
        f"{_guides(model.guides.anchor)}"
        "</section>"
    )


def _identity_section(model: PageModel) -> str:
    if not model.conditions.mtls:
        return ""

    heading = "<h2>Get a client certificate</h2>"
    explain = (
        "<p>This box was built to require one. Reaching this network is not enough to "
        "use Loom: every route refuses a connection that presents no certificate of its "
        "own. The password below is on the screen attached to the box, and it changes "
        "every day.</p>"
    )

    if not model.conditions.secure and model.urls.secure:
        # The form is deliberately not offered here. The answer to it is a PKCS#12 file
        # with an unencrypted private key in it, and this connection is plaintext on a
        # segment that -- on a --wifi box -- is everyone in radio range.
        return (
            f'<section id="identity">{heading}{explain}'
            '<div class="notice warn"><strong>Not over this connection.</strong>'
            "<p>A certificate comes with its own private key, so it is only handed out "
            "over an encrypted connection. Install the certificate above first, then "
            "come back here:</p>"
            f'<p><a class="download" href="{escape(model.urls.secure)}#identity">'
            "Continue securely</a></p>"
            "<p>If you have not installed the certificate above, your browser will warn "
            "you once. That warning is the one thing the section above exists to "
            "remove.</p></div></section>"
        )

    if not model.urls.secure:
        # Reachable on one supported configuration: `portal.nix` sets
        # `LOOM_PORTAL_MTLS` from `cfg.mtls.enable` alone, while the TLS listener also
        # needs `cfg.portal.tls.enable`, which is a documented option. The page says so
        # rather than serving a private key in the clear or pretending to.
        return (
            f'<section id="identity">{heading}{explain}'
            '<div class="notice bad"><strong>Not configured.</strong>'
            "<p>This box has no encrypted listener, so it will not hand out a "
            "certificate. Ask the operator to issue one from the console with "
            "<code>loom-client-certificate</code>.</p></div></section>"
        )

    return (
        f'<section id="identity">{heading}{explain}'
        '<form method="post" action="/certificate">'
        '<label for="password">Password from the box&rsquo;s screen</label>'
        '<input id="password" name="password" type="password" '
        'autocomplete="off" autocapitalize="off" autocorrect="off" '
        'spellcheck="false" required>'
        '<label for="label">A name for this certificate (optional)</label>'
        '<input id="label" name="label" type="text" placeholder="visitor" '
        'autocapitalize="off" autocorrect="off" spellcheck="false" '
        'maxlength="24" pattern="[a-z0-9][a-z0-9-]*">'
        '<div class="buttons">'
        '<button class="primary" type="submit" name="format" value="p12">'
        "Get my certificate</button>"
        '<button class="plain" type="submit" name="format" value="zip">'
        "All files, as a .zip</button>"
        "</div>"
        "</form>"
        "<p>The certificate is valid for a few days and nothing renews it. Come back "
        "here for another one.</p>"
        '<div class="notice warn"><strong>The identity carries no trust.</strong>'
        "<p>Installing it lets Loom accept you. It does not make Loom&rsquo;s own "
        "certificate trusted &mdash; that is the section above, and it is a separate "
        "step.</p></div>"
        f"{_guides(model.guides.identity)}"
        "</section>"
    )


def _guides(guides: list[InstallGuide]) -> str:
    if not guides:
        return ""
    blocks = []
    for guide in guides:
        steps = "".join(f"<li>{escape(step)}</li>" for step in guide.steps)
        note = f'<p class="note">{escape(guide.note)}</p>' if guide.note else ""
        blocks.append(
            f"<details><summary>{escape(guide.platform)}</summary>"
            f"<ol>{steps}</ol>{note}</details>"
        )
    return f'<div class="guides">{"".join(blocks)}</div>'


def _finish_section(model: PageModel) -> str:
    """The last thing on the page, and the only control a visitor who wants nothing from
    this box will ever use.

    Last, deliberately. Pressing it makes this device's next connectivity probe succeed,
    and a captive-portal sheet closes the instant that happens -- within sixty seconds
    on Apple, whatever the visitor happens to be reading. So nothing anybody needs may
    sit below it, and the label has to carry the whole message on its own, because the
    page that follows the press may never be seen.

    A form and not a link, for the same reason turned around: a webview that prefetches,
    a reload, or a browser that follows links on hover would close the sheet while the
    visitor was still reading. And not a script -- this page has none, and
    `tests/test_page.py` bans `<script` outright rather than merely `<script src=`.

    The honesty copy sits above the button rather than after it, since above it is the
    only place it can be read.
    """
    if model.conditions.validated:
        return (
            '<section id="done">'
            "<h2>This device has stopped asking</h2>"
            "<p>It will no longer warn you that this network has no internet. It "
            "still has none &mdash; this box serves Loom and nothing else. The page "
            f"stays at <code>{escape(model.urls.portal)}</code>.</p>"
            "</section>"
        )
    return (
        '<section id="done">'
        "<h2>Stop the &ldquo;no internet&rdquo; warning</h2>"
        "<p>Your device keeps checking for internet behind this box, keeps finding "
        "none, and warns you about it &mdash; and a phone may quietly go back to "
        "mobile data, which cannot reach Loom at all. This tells it to stop "
        "checking.</p>"
        '<div class="notice warn"><strong>This is not internet.</strong>'
        "<p>There is still nothing behind this box but Loom. The button only stops "
        "your device asking, so everything that is not Loom will keep failing and "
        "your device will no longer tell you why. Your sign-in window may close the "
        "moment you press it &mdash; the page stays at "
        f"<code>{escape(model.urls.portal)}</code>.</p></div>"
        '<form method="post" action="/done">'
        '<button class="primary" type="submit">'
        "I&rsquo;m done here &mdash; stop the warning</button>"
        "</form>"
        "</section>"
    )


def _footer(model: PageModel) -> str:
    return (
        "<footer>"
        f"<p>This page is at <code>{escape(model.urls.portal)}</code></p>"
        "<p>There is no internet behind this box. It serves Loom and nothing else, "
        "and it is not a route to anywhere.</p>"
        "</footer>"
    )


def _stylesheet(accent: str) -> str:
    """One inline stylesheet, light and dark.

    `prefers-color-scheme` rather than a toggle, matching the frontend (`theme.ts` sets
    `colorSchemeSelector: "media"`). A visitor meeting this page for ten seconds should
    not have to configure it.
    """
    return (
        ":root{"
        f"--accent:{accent};"
        "--layer:#f5f5f2;--fg:#31312e;--muted:#5a5a57;"
        "--card:#ffffff;--rule:#dededa;"
        "--warn:#ff8800;--bad:#cc0000;--good:#007e33;"
        "}"
        "@media (prefers-color-scheme: dark){:root{"
        "--layer:#1a1a17;--fg:#e8e8e5;--muted:#9a9a95;"
        "--card:#282825;--rule:#3a3a37;"
        "--warn:#ffbb33;--bad:#ff4444;--good:#00c851;"
        "}}"
        "*{box-sizing:border-box}"
        "body{margin:0;background:var(--layer);color:var(--fg);"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Roboto','Oxygen',"
        "'Ubuntu','Cantarell','Fira Sans','Droid Sans','Helvetica Neue',sans-serif;"
        "line-height:1.5;-webkit-font-smoothing:antialiased}"
        ".page{max-width:44rem;margin:0 auto;padding:1.5rem 1.25rem 4rem}"
        ".mark{display:flex;align-items:center;gap:1rem;margin-bottom:2rem}"
        ".mark img{border-radius:12px}"
        "h1{font-size:1.35rem;margin:0}"
        "h2{font-size:1.1rem;margin:0 0 .5rem}"
        ".tag{margin:0;color:var(--muted);font-size:.85rem}"
        "section{background:var(--card);border:1px solid var(--rule);"
        "border-radius:12px;padding:1.25rem;margin-bottom:1.25rem}"
        ".act{text-align:center}"
        ".act p{color:var(--muted);font-size:.9rem;margin:1rem 0 0;text-align:left}"
        "a.primary,button.primary{display:inline-block;background:var(--accent);"
        "color:#1a1a17;font-weight:600;font-size:1.1rem;text-decoration:none;"
        "padding:.85rem 2rem;border:0;border-radius:10px;cursor:pointer}"
        "a.download{display:inline-block;background:var(--accent);color:#1a1a17;"
        "font-weight:600;text-decoration:none;padding:.6rem 1.1rem;border-radius:8px}"
        "a.plain,button.plain{display:inline-block;color:var(--fg);"
        "background:transparent;text-decoration:underline;padding:.6rem 1.1rem;"
        "border:1px solid var(--rule);border-radius:8px;margin-left:.5rem;"
        "font-size:.9rem;cursor:pointer}"
        ".buttons{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;"
        "margin-top:1rem}"
        ".buttons .plain{margin-left:0}"
        "form{margin:1rem 0 0}"
        "label{display:block;font-size:.85rem;color:var(--muted);margin:.75rem 0 .25rem}"
        "input{width:100%;padding:.7rem;font-size:1rem;color:var(--fg);"
        "background:var(--layer);border:1px solid var(--rule);border-radius:8px}"
        ".notice{border-left:4px solid var(--rule);border-radius:6px;"
        "padding:.75rem 1rem;margin:1rem 0;background:var(--layer)}"
        ".notice p{margin:.4rem 0 0;font-size:.9rem}"
        ".notice.good{border-left-color:var(--good)}"
        ".notice.warn{border-left-color:var(--warn)}"
        ".notice.bad{border-left-color:var(--bad)}"
        "code{font-family:source-code-pro,Menlo,Monaco,Consolas,'Courier New',monospace;"
        "font-size:.85em;word-break:break-all}"
        ".fp{font-size:.85rem;color:var(--muted)}"
        ".guides{margin-top:1rem}"
        "details{border-top:1px solid var(--rule);padding:.6rem 0}"
        "summary{cursor:pointer;font-weight:600;font-size:.95rem}"
        "details ol{margin:.6rem 0 0;padding-left:1.3rem;font-size:.9rem}"
        "details li{margin-bottom:.35rem}"
        ".note{font-size:.85rem;color:var(--muted);margin:.5rem 0 0}"
        "footer{color:var(--muted);font-size:.8rem;text-align:center}"
    )
