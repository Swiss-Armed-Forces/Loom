"""Test doubles for the two seams this package has.

Both are passed in rather than patched into place, which is the repository's standing
rule about monkeypatching and the reason `build_portal` takes a `clock` and a `spool` at
all. Nothing here replaces anything at runtime behind the code's back.

Both are subclasses rather than stand-alone imitations, for the reason
`loom_ready.tests.doubles` gives: the real constructor is the one that gets exercised,
so a parameter added to `Spool` or `Clock` breaks the double at the call rather than
letting the suite drift quietly away from what the service does.

`doubles_portal` rather than `doubles`, which is what every other suite here calls this
file, for two reasons that both have to hold: `appliance-pytest` runs all of them in one
pytest session, so every module basename under `appliancePytestPaths` shares one
namespace and a second `doubles.py` would shadow the first; and pylint sorts a loose
module above the package being linted, so a name that comes after `loom_portal`
alphabetically is a `wrong-import-order` on every file that imports it.
"""

import os
from collections.abc import Callable
from typing import NamedTuple

from loom_portal.clock import Clock
from loom_portal.settings import PortalLimits, PortalSettings, PortalUrls
from loom_portal.spool import BundleFormat, IssuanceOutcome, IssuanceState, Spool

PASSWORD = "harbor.ritual.cobalt.fenced"
PREVIOUS_PASSWORD = "lantern.quartz.meadow.sprig"

# A certificate's worth of bytes. Nothing parses it; the suite only checks that what went
# into the spool directory is what came back out.
P12_BYTES = b"\x30\x82fake pkcs12"


class FakeClock(Clock):
    """Time that only moves when something asks it to.

    `sleep` advances a stored float instead of blocking, so a 45-second deadline costs
    450 iterations of a loop rather than 45 seconds of a build. `on_sleep` is what lets
    `test_spool.py` play the part of the root issuer: a callback that drops a bundle
    into place on the third tick, without a thread.
    """

    def __init__(
        self, start: float = 1000.0, on_sleep: Callable[[float], None] | None = None
    ):
        self.current = start
        self.on_sleep = on_sleep
        self.slept = 0.0

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.current += seconds
        self.slept += seconds
        if self.on_sleep is not None:
            self.on_sleep(self.current)


class IssuedRequest(NamedTuple):
    """One call `FakeSpool` was asked to make."""

    label: str
    want: BundleFormat


class FakeSpool(Spool):
    """A spool that answers at once, and remembers what it was asked.

    The record is half the point: "a wrong password creates no request" is a property of
    `Portal` that can only be observed from here.
    """

    def __init__(self, outcome: IssuanceOutcome | None = None):
        # Paths that do not exist: nothing in this double touches the filesystem, and a
        # test that accidentally reached the real implementation should fail loudly.
        super().__init__(
            requests_dir="/nonexistent/requests",
            bundles_dir="/nonexistent/bundles",
            clock=FakeClock(),
            max_in_flight=2,
            timeout_s=1.0,
        )
        self.outcome = outcome or IssuanceOutcome(
            state=IssuanceState.DELIVERED,
            bundle=P12_BYTES,
            filename="visitor-0123abcd.p12",
            content_type="application/x-pkcs12",
        )
        self.issued: list[IssuedRequest] = []

    def issue(self, label: str, want: BundleFormat) -> IssuanceOutcome:
        self.issued.append(IssuedRequest(label=label, want=want))
        return self.outcome


def settings_for(
    root,
    *,
    mtls: bool = False,
    secure_url: str = "",
    limits: PortalLimits | None = None,
) -> PortalSettings:
    """A settings object pointed at a temporary state directory, with the spool made.

    The default delay on a wrong password is zero here and a second on a box: every test
    drives a fake clock, so the pause would be free, but a test that asserts on
    `clock.slept` wants to be the one that asks for it.
    """
    settings = PortalSettings(
        state_dir=str(root),
        mtls=mtls,
        urls=PortalUrls(secure=secure_url),
        limits=limits or PortalLimits(wrong_password_delay_s=0.0),
    )
    os.makedirs(settings.requests_dir, exist_ok=True)
    os.makedirs(settings.bundles_dir, exist_ok=True)
    return settings


def write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def write_passwords(
    settings: PortalSettings,
    current: str = PASSWORD,
    previous: str = PREVIOUS_PASSWORD,
) -> None:
    write(settings.password_path, current + "\n")
    write(settings.previous_password_path, previous + "\n")


def write_anchor(settings: PortalSettings, fingerprint: str | None = None) -> None:
    write(
        settings.anchor_path,
        "-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----\n",
    )
    write(
        settings.fingerprint_path,
        (fingerprint or ":".join(["AB"] * 32)) + "\n",
    )


def place_bundle(
    settings: PortalSettings, token: str, stem: str = "visitor-0123abcd"
) -> None:
    """What the root issuer leaves behind when it succeeds."""
    bundle = os.path.join(settings.bundles_dir, token)
    os.makedirs(bundle, exist_ok=True)
    with open(os.path.join(bundle, stem + ".p12"), "wb") as handle:
        handle.write(P12_BYTES)
    write(os.path.join(bundle, stem + ".crt"), "cert\n")
    write(os.path.join(bundle, stem + ".key"), "key\n")
    write(os.path.join(bundle, "loom-server-ca.pem"), "anchor\n")
    write(os.path.join(bundle, "README.txt"), "readme\n")


def place_error(settings: PortalSettings, token: str, reason: str) -> None:
    """And what it leaves behind when it refuses."""
    write(os.path.join(settings.bundles_dir, token + ".error"), reason + "\n")


def pending_tokens(settings: PortalSettings) -> list[str]:
    """The tokens with a request file waiting.

    The service itself may not do this -- the directory is mode 0730 on a box, so it can
    create and unlink by name and never enumerate -- but the suite runs as whoever is
    building, and "no request was created" is the assertion that matters most here.
    """
    return sorted(
        name[: -len(".req")]
        for name in os.listdir(settings.requests_dir)
        if name.endswith(".req")
    )
