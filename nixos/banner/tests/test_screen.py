"""Which sections appear, and in which order.

The order is the one property of this screen that cannot be checked by looking at it on
a console with room to spare: it only shows up on a console without room, where the top
rows are gone and what is left has to be the rows somebody needed.
"""

import pytest

from loom_banner.facts import Box, KeyGuard, Live, Portal, Wifi
from loom_banner.screen import compose

SPARK = Box(
    tag="1.5.0-rc6",
    platform="NVIDIA DGX Spark",
    key_guard=KeyGuard(action="warn", grace=20, arm_deadline=120),
    portal=Portal(host="portal.loom", issues_certificates=True),
)

RUNNING = Live(
    wired_interface="loom0",
    subnet="10.160.227.0/24",
    summary="Loom: ready.",
    key_guard="armed",
    recovery_passphrase="8euwj-4qkws-yvwk7-9rs7k-typst-jxae4",
    portal_password="backspin.finisher.taste.unsmooth",
)

QR = ("▄▄▄▄▄▄▄", "█ ▄▄▄ █", "▀▀▀▀▀▀▀")


def titles(box: Box, live: Live, **kwargs) -> list[str]:
    return [
        section.title for section in compose(box, live, "06:57 UTC", **kwargs).sections
    ]


class TestOrder:
    def test_the_rows_to_read_are_the_rows_at_the_bottom(self):
        assert titles(SPARK, RUNNING) == ["Connect", "Write these down", "This box"]

    def test_the_card_sits_above_the_secrets(self):
        """A half-scrolled QR is unscannable anyway; a half-scrolled passphrase costs
        the reader the box."""
        ordered = titles(SPARK, RUNNING, qr=QR)
        assert ordered.index("Scan to join the WiFi") < ordered.index(
            "Write these down"
        )


class TestEmptiness:
    def test_a_section_with_nothing_in_it_costs_no_row(self):
        # A box in its first seconds: no network.conf yet, no cluster, no key, no
        # password. Every rule would be a rule over nothing.
        bare = compose(SPARK, Live(), painted="")
        assert [section.title for section in bare.sections] == []

    def test_the_timestamp_alone_is_worth_the_section(self):
        bare = compose(SPARK, Live(), "06:57 UTC")
        assert [section.title for section in bare.sections] == ["This box"]

    def test_no_card_means_no_rule_for_one(self):
        assert "Scan to join the WiFi" not in titles(SPARK, RUNNING)

    def test_a_box_with_no_cluster_yet_says_nothing_about_it(self):
        """`loom_ready.text` leaves the summary empty until it has a number on it, and
        this screen has a hard height budget."""
        composed = compose(
            SPARK, Live(wired_interface="loom0", subnet="x"), "06:57 UTC"
        )
        assert composed.identity == ("Loom appliance 1.5.0-rc6 -- NVIDIA DGX Spark",)


class TestIdentity:
    def test_the_tag_and_the_platform_share_a_row(self):
        composed = compose(SPARK, RUNNING, "06:57 UTC")
        assert composed.identity[0] == "Loom appliance 1.5.0-rc6 -- NVIDIA DGX Spark"

    def test_the_summary_is_placed_verbatim(self):
        """`loom_ready.text` owns its shape, including that it is one line with no
        backslash in it.

        Reformatting it here would be a second opinion on both.
        """
        composed = compose(SPARK, RUNNING, "06:57 UTC")
        assert composed.identity[-1] == "Loom: ready."

    def test_a_box_without_the_ai_services_says_so(self):
        composed = compose(
            Box(tag="1.5.0", platform="Intel NUC 12 Pro", runs_ai=False),
            RUNNING,
            "06:57 UTC",
        )
        assert any("No AI on this box" in line for line in composed.identity)


class TestSecrets:
    def secrets(self, box: Box, live: Live):
        sections = {s.title: s for s in compose(box, live, "06:57 UTC").sections}
        return sections["Write these down"]

    def test_everything_transcribable_is_in_one_block(self):
        wifi_box = Box(
            tag="1.5.0",
            platform="GMKtec EVO-X2",
            wifi=Wifi(ssid="loom-appliance", psk="correct.horse.battery"),
            portal=Portal(host="portal.loom", issues_certificates=True),
        )
        rows = self.secrets(wifi_box, RUNNING).rows
        assert [row.label for row in rows] == [
            "WiFi network:",
            "WiFi passphrase:",
            "LUKS recovery passphrase:",
            "Portal password (today):",
        ]

    def test_a_passphrase_is_marked_to_be_typed_and_a_network_name_is_not(self):
        wifi_box = Box(
            tag="1.5.0",
            platform="GMKtec EVO-X2",
            wifi=Wifi(ssid="loom-appliance", psk="correct.horse.battery"),
        )
        marked = {row.label: row.secret for row in self.secrets(wifi_box, Live()).rows}
        assert marked == {"WiFi network:": False, "WiFi passphrase:": True}

    def test_an_image_that_cannot_issue_certificates_says_where_to(self):
        """Pointing a visitor at a page that refuses every plaintext POST would be worse
        than saying nothing; the operator gets the route that does work."""
        notes = self.secrets(
            Box(
                tag="1.5.0",
                platform="NVIDIA DGX Spark",
                portal=Portal(host="portal.loom", issues_certificates=False),
            ),
            Live(portal_password="backspin.finisher"),
        ).notes
        assert any("loom-client-certificate" in note for note in notes)
        assert not any("portal.loom" in note for note in notes)


class TestKeyGuard:
    @pytest.mark.parametrize(
        ("action", "state", "expected"),
        [
            ("poweroff", "armed", "armed -- removing the key powers off after 20s"),
            ("warn", "armed", "armed -- removing the key only warns"),
            ("poweroff", "disarmed", "disarmed until the next boot"),
            ("poweroff", "anything-else", "idle -- no USB key present"),
        ],
    )
    def test_it_promises_what_this_image_will_actually_do(
        self, action, state, expected
    ):
        """A banner promising a poweroff on an image whose guard only warns is the one
        claim on this screen an operator can disprove by pulling the stick."""
        box = Box(
            tag="1.5.0",
            platform="NVIDIA DGX Spark",
            key_guard=KeyGuard(action=action, grace=20),
        )
        sections = {
            s.title: s for s in compose(box, Live(key_guard=state), "").sections
        }
        assert sections["This box"].rows[0].value == expected

    def test_a_box_with_no_guard_at_all_says_nothing(self):
        """A box booted on the recovery passphrase has no key, so its guard never
        arms -- and a row claiming otherwise would promise protection it lacks."""
        sections = {s.title: s for s in compose(SPARK, Live(), "06:57 UTC").sections}
        assert [row.label for row in sections["This box"].rows] == ["Screen painted:"]


class TestPainted:
    def test_the_screen_says_when_it_was_drawn(self):
        """Without it a stale screen and a live one are identical, and this one is only
        repainted while nobody has pressed a key."""
        sections = {s.title: s for s in compose(SPARK, RUNNING, "06:57 UTC").sections}
        painted = [
            row for row in sections["This box"].rows if row.label == "Screen painted:"
        ]
        assert painted[0].value == "06:57 UTC"
