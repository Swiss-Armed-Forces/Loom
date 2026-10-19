"""Which sections the screen has, and in what order.

A pure function of the facts, so that the one property that matters can be asserted
without a VM: **the rows somebody has to read are the rows nearest the bottom.** The
issue is written straight to the VT with no paging, so a banner taller than the console
loses its *first* rows -- which makes the tail the only position that cannot scroll
away, and puts the mark at the top where it is the thing that can be spared.

The QR sits above the secrets for the same reason. When the screen is too short, a half-
scrolled QR is already unscannable, so losing it costs nothing a reader could have used;
losing a passphrase they were copying costs them the box.
"""

from dataclasses import dataclass, field

from loom_banner.facts import GUARD_ARMED, GUARD_DISARMED, Box, Live


@dataclass(frozen=True)
class Row:
    """One label and one value, in the aligned column."""

    label: str
    value: str
    secret: bool = False


@dataclass(frozen=True)
class Section:
    """A rule, and what is under it."""

    title: str
    style: str = ""
    rows: tuple[Row, ...] = ()
    notes: tuple[str, ...] = ()
    card: tuple[str, ...] = ()

    @property
    def empty(self) -> bool:
        return not (self.rows or self.notes or self.card)


@dataclass(frozen=True)
class Screen:
    """Everything below the mark."""

    identity: tuple[str, ...] = field(default_factory=tuple)
    sections: tuple[Section, ...] = field(default_factory=tuple)


def compose(box: Box, live: Live, painted: str, qr: tuple[str, ...] = ()) -> Screen:
    """The whole screen, bar the mark itself."""
    return Screen(
        identity=_identity(box, live),
        sections=tuple(
            section
            for section in (
                _connect(live),
                _wifi(qr),
                _secrets(box, live),
                _this_box(box, live, painted),
            )
            if not section.empty
        ),
    )


def _identity(box: Box, live: Live) -> tuple[str, ...]:
    """What the box is, and how far it has got.

    The summary is placed verbatim and never reformatted: `loom_ready.text` owns its
    shape, including the guarantee that it is one line with no backslash in it, and
    it is empty until there is a number on it.
    """
    lines = [f"Loom appliance {box.tag} -- {box.platform}"]
    if not box.runs_ai:
        lines.append("No AI on this box: no summaries, translation or semantic search.")
    if not box.meets_resource_minimum:
        lines.append(
            "Below the documented memory minimum -- running without resource limits."
        )
    if live.summary:
        lines.append(live.summary)
    return tuple(lines)


def _connect(live: Live) -> Section:
    """The two facts somebody with a laptop needs.

    http rather than https, and the friendlier of the two now that both work: the
    certificate is self-signed, so the https spelling costs whoever reads this an
    interstitial, and it is the URL the captive portal sends a phone to.
    """
    if not (live.wired_interface and live.subnet):
        return Section("Connect")
    return Section(
        "Connect",
        notes=(
            f"Plug a laptop into {live.wired_interface} and browse "
            "http://frontend.loom",
            f"DHCP and *.loom are served on {live.subnet}",
        ),
    )


def _wifi(qr: tuple[str, ...]) -> Section:
    """The card, with the credentials themselves kept in `Write these down`.

    Named for what scanning does rather than for what the block is, because the phone is
    already out by the time anybody reads the rule.
    """
    if not qr:
        return Section("Scan to join the WiFi")
    return Section("Scan to join the WiFi", card=qr)


def _secrets(box: Box, live: Live) -> Section:
    """Everything that has to be transcribed, in one shape and one column.

    WiFi first: it is the only one of these that is needed *before* the box is
    reachable at all, and on a --wifi box it is what the card above was for.
    """
    rows: list[Row] = []
    notes: list[str] = []

    if box.wifi.ssid:
        rows.append(Row("WiFi network:", box.wifi.ssid))
        rows.append(Row("WiFi passphrase:", box.wifi.psk, secret=True))

    if live.recovery_passphrase:
        rows.append(
            Row("LUKS recovery passphrase:", live.recovery_passphrase, secret=True)
        )
        notes.append(
            "Without the stick, the recovery passphrase is the only way into this disk."
        )

    if live.portal_password:
        rows.append(Row("Portal password (today):", live.portal_password, secret=True))
        if box.portal.issues_certificates:
            notes.append(
                f"Visitors need the password at http://{box.portal.host} to get a "
                "certificate."
            )
        else:
            # The page degrades to "Not configured" and refuses every plaintext POST,
            # because a PKCS#12 carries an unencrypted private key. Pointing a visitor
            # at a URL that can never issue one would be worse than saying nothing.
            notes.append("This image issues no certificates from the portal.")
            notes.append(
                "Issue one here: loom-client-certificate --name NAME --out-dir DIR"
            )

    return Section("Write these down", rows=tuple(rows), notes=tuple(notes))


def _this_box(box: Box, live: Live, painted: str) -> Section:
    """State that is true now and may not be in a minute.

    `Screen painted` is the row that makes the rest of them checkable. agetty paints the
    issue once and then blocks on a keypress, and `loom-banner-refresh` will not repaint
    a console somebody has touched -- so a screen showing yesterday's password is
    indistinguishable from a live one without a timestamp on it.
    """
    rows: list[Row] = []
    notes: list[str] = []

    guard = _guard(box, live)
    if guard:
        rows.append(Row("USB key guard:", guard))
    if live.key_guard_pending:
        # The budget, not a countdown: this screen is painted once, and a countdown
        # on it would be wrong within the second.
        notes.append(
            f"This box powers off {box.key_guard.arm_deadline}s after boot unless "
            "the key arms."
        )
        notes.append("Run 'loom-key-guard disarm' to keep it up.")
    if painted:
        rows.append(Row("Screen painted:", painted))

    return Section("This box", rows=tuple(rows), notes=tuple(notes))


def _guard(box: Box, live: Live) -> str:
    """What the guard will actually do, not what the usual image does.

    A banner promising a poweroff on an image whose guard only warns is the one claim on
    this screen an operator can disprove by pulling the stick.
    """
    if not live.key_guard:
        return ""
    if live.key_guard == GUARD_ARMED:
        if box.key_guard.action == "poweroff":
            return f"armed -- removing the key powers off after {box.key_guard.grace}s"
        return "armed -- removing the key only warns"
    if live.key_guard == GUARD_DISARMED:
        return "disarmed until the next boot"
    return "idle -- no USB key present"
