"""Everything the portal was told, in one value.

Assembled once in `__main__` from the environment the Nix wrapper sets and from the
command line, then passed down. Nothing below this module reads `os.environ`, which is
what lets the suite construct a settings object by hand and get a portal that behaves
exactly like the one on a box.

The paths are derived rather than declared one by one, because the layout is a contract
with two things outside this package -- portal.nix's tmpfiles rules and the root
issuer's shell script -- and three copies of it would be three places to get wrong.

Grouped into four values rather than kept flat, so that each of them is a thing with a
name: what the page links to, what it looks like, what it will not exceed, and where it
reads and writes. `page.py` takes two of them straight out of here, so the page and the
service cannot disagree about a URL or about the brand.
"""

import os
from dataclasses import dataclass, field

# Where the appliance publishes what this service reads. portal.nix creates it.
DEFAULT_STATE_DIR = "/run/loom-portal"

# The names inside it.
ANCHOR_NAME = "anchor.pem"
FINGERPRINT_NAME = "anchor.sha256"
PASSWORD_NAME = "password"
PREVIOUS_PASSWORD_NAME = "password.previous"
REQUESTS_NAME = "requests"
BUNDLES_NAME = "bundles"

# How long the page waits for the root issuer before telling the visitor to try again.
#
# Shorter than the issuer's own `TimeoutStartSec`, deliberately: an `openssl genrsa 4096`
# on an appliance that is also indexing takes a few seconds, and anything past this is a
# `kubectl` that is not going to answer. A page that says "try again" is better than one
# that spins, and nginx's `proxy_read_timeout` on this route is longer still so the
# answer actually reaches the visitor.
DEFAULT_ISSUE_TIMEOUT_S = 45.0

# How many certificates may be in flight at once.
#
# Counted in this process rather than by listing the spool, because the spool directory is
# deliberately not readable by this service -- see `spool.py`. Two is enough for a room
# full of people taking turns and few enough that nobody can make the box spend all its
# CPU generating keys.
DEFAULT_MAX_IN_FLIGHT = 2

# The token bucket over password attempts. Four EFF words is about 51 bits, so online
# guessing is not the threat being defended against here; CPU is, and so is a visitor
# holding the form open on a key-repeat.
DEFAULT_ATTEMPTS = 10
DEFAULT_ATTEMPT_WINDOW_S = 60.0

# A flat pause on a wrong answer. Not a security control -- the bucket above is -- but it
# stops a mistyped password from being retried thirty times in a second by a browser that
# resubmits on its own.
DEFAULT_WRONG_PASSWORD_DELAY_S = 1.0

# The logo amber, `loom.branding.amberRgb` and `Frontend/public/favicon.svg`. Declared
# here rather than in `page.py` so there is one copy of it in this package; portal.nix
# passes the box's own value in, so a brand change moves both at once.
DEFAULT_ACCENT = "#f7b718"


@dataclass(frozen=True)
class PortalUrls:
    """The absolute URLs the page prints.

    All three are computed in Nix, because only Nix knows whether this image serves
    plain http at all -- a `--require-client-cert` box does not, so `frontend` is https
    there and http everywhere else.
    """

    frontend: str = "http://frontend.loom/"
    # Where this page is, printed in the footer so a visitor can come back to it without
    # making their phone re-run a connectivity probe.
    portal: str = "http://portal.loom/"
    # Empty on an image with no TLS listener of its own, which is every image but the
    # mutual TLS one. The page then offers no "reopen securely" link, because there is
    # nothing to reopen into.
    secure: str = ""


@dataclass(frozen=True)
class PortalBrand:
    """What the page is drawn as."""

    # The release the box was built from, printed under the mark.
    tag: str = "dev"
    accent: str = DEFAULT_ACCENT
    # The Loom mark, as a PNG in the store. branding.nix has already checked that it is
    # one rather than an unmaterialised git-lfs pointer.
    logo_path: str = ""


@dataclass(frozen=True)
class PortalLimits:
    """What the service will not exceed, whoever asks."""

    issue_timeout_s: float = DEFAULT_ISSUE_TIMEOUT_S
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT
    attempts: int = DEFAULT_ATTEMPTS
    attempt_window_s: float = DEFAULT_ATTEMPT_WINDOW_S
    wrong_password_delay_s: float = DEFAULT_WRONG_PASSWORD_DELAY_S


@dataclass(frozen=True)
class PortalSettings:
    """What this box is, and what the page may offer."""

    # Where the server binds. Loopback: nginx is what faces the appliance segment.
    listen_address: str = "127.0.0.1"
    port: int = 18082

    urls: PortalUrls = field(default_factory=PortalUrls)
    brand: PortalBrand = field(default_factory=PortalBrand)
    limits: PortalLimits = field(default_factory=PortalLimits)

    state_dir: str = DEFAULT_STATE_DIR

    # Whether this box requires a client certificate. The whole issuance half of the page
    # and of the router exists only when it does.
    mtls: bool = False

    @property
    def anchor_path(self) -> str:
        return os.path.join(self.state_dir, ANCHOR_NAME)

    @property
    def fingerprint_path(self) -> str:
        return os.path.join(self.state_dir, FINGERPRINT_NAME)

    @property
    def password_path(self) -> str:
        return os.path.join(self.state_dir, PASSWORD_NAME)

    @property
    def previous_password_path(self) -> str:
        return os.path.join(self.state_dir, PREVIOUS_PASSWORD_NAME)

    @property
    def requests_dir(self) -> str:
        return os.path.join(self.state_dir, REQUESTS_NAME)

    @property
    def bundles_dir(self) -> str:
        return os.path.join(self.state_dir, BUNDLES_NAME)
