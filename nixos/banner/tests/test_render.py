"""The four rules the screen cannot break, asserted against rendered bytes."""

from io import StringIO

import pytest
from banner_text import columns, visible

from loom_banner import render


class TestBackslash:
    """Agetty eats a backslash as the start of an escape of its own.

    Every primitive refuses one rather than letting it reach the file, because the value
    most likely to contain a surprising character is a passphrase and a passphrase that
    is silently one character short cannot be recovered from the screen it was read on.
    """

    @pytest.mark.parametrize(
        "call",
        [
            lambda: render.row("Label:", "back\\slash"),
            lambda: render.row("back\\slash:", "value"),
            lambda: render.note("back\\slash"),
            lambda: render.rule("back\\slash"),
            lambda: render.card(["back\\slash"]),
            lambda: render.danger(["back\\slash"]),
        ],
    )
    def test_refused_everywhere(self, call):
        with pytest.raises(render.BannerError, match="backslash"):
            call()

    def test_the_whole_screen_is_clean(self, paint):
        painted = paint(
            render.rule("Write these down"),
            render.row("LUKS recovery passphrase:", "8euwj-4qkws-yvwk7"),
            render.note("Without the stick, this is the only way in."),
        )
        assert "\\" not in painted


class TestWidth:
    def test_a_rule_reaches_the_margin(self, paint):
        line = visible(paint(render.rule("Connect"))).rstrip("\n")
        assert columns(line) == render.WIDTH
        assert line.startswith("  ── Connect ─")

    def test_a_title_too_long_for_a_rule_is_refused(self):
        with pytest.raises(render.BannerError, match="no room"):
            render.rule("x" * render.WIDTH)

    def test_a_label_over_the_column_is_refused(self):
        # Silently pushing one row out of line would cost more than the longer label
        # is worth: the column is the whole reason the block can be read downwards.
        with pytest.raises(render.BannerError, match="over the"):
            render.row("x" * render.LABEL_COLUMN + ":", "value")

    def test_the_longest_real_label_fits(self):
        # The longest label any section asks for. If this ever stops fitting, the
        # column moves -- it does not get quietly overrun.
        rendered = visible(render.row("LUKS recovery passphrase:", "x").plain)
        assert rendered.index("x") == render.INDENT + render.LABEL_COLUMN


class TestEmphasis:
    def test_a_secret_is_reverse_video_and_nothing_else_is(self, paint):
        painted = paint(render.row("Portal password (today):", "backspin.finisher"))
        assert "\x1b[7m" not in painted

        painted = paint(
            render.row("Portal password (today):", "backspin.finisher", secret=True)
        )
        assert "\x1b[7mbackspin.finisher\x1b[0m" in painted

    def test_the_field_is_the_value_and_not_the_padding(self, paint):
        """A short secret is a short field.

        rich's grid would pad every cell in a column to the width of its widest and put
        that padding inside the style, turning a short passphrase into a long reverse-
        video bar with nothing in most of it.
        """
        painted = paint(
            render.row("WiFi network:", "loom", secret=True),
            render.row("WiFi passphrase:", "a-much-longer-passphrase", secret=True),
        )
        assert "\x1b[7mloom\x1b[0m" in painted

    def test_the_danger_block_is_a_rectangle(self, paint):
        painted = paint(*render.danger(["DEBUG IMAGE", "This box runs an SSH server."]))
        lines = [line for line in visible(painted).split("\n") if line.strip()]
        assert len({columns(line) for line in lines}) == 1
        # The byte the VM test greps for: red as a background, not only a foreground.
        assert "\x1b[1;37;41m" in painted

    def test_colour_is_dropped_when_nothing_is_watching(self, paint):
        """`loom-info > banner.txt` stays readable."""
        painted = paint(render.row("Label:", "value", secret=True), colour=False)
        assert "\x1b[" not in painted


class TestMarkup:
    def test_bracketed_values_survive(self, paint):
        """Rich's markup parser would eat these.

        An SSID is whatever somebody typed into a build flag, and a bracketed run is
        exactly what the parser claims.
        """
        painted = visible(paint(render.row("WiFi network:", "loom-[ap]-1")))
        assert "loom-[ap]-1" in painted

    def test_urls_and_addresses_are_not_recoloured(self, paint):
        """Rich's highlighter would pick these apart into three colours."""
        painted = paint(render.note("DHCP and *.loom are served on 10.160.227.0/24"))
        assert "\x1b[" not in painted


class TestPalette:
    def test_the_redefinition_names_both_indices(self):
        # Bold promotes index 3 to index B, and a 512-glyph font makes which one a
        # given VT lands on not worth predicting.
        sequence = render.palette("f7b718")
        assert "\033]P3f7b718" in sequence
        assert "\033]PBf7b718" in sequence
        # Pure white, so the QR card is a card rather than light grey.
        assert "\033]P7ffffff" in sequence

    @pytest.mark.parametrize("bad", ["", "f7b71", "f7b7188", "nothex"])
    def test_a_colour_that_is_not_one_is_refused(self, bad):
        with pytest.raises(render.BannerError, match="hex"):
            render.palette(bad)


class TestColour:
    def test_the_issue_file_is_told_it_is_a_vt(self):
        # The redirection that builds the issue hides the console, and without this
        # the one screen the colour exists for renders plain.
        decided = render.Colour.decide(StringIO(), {"LOOM_INFO_COLOR": "vt"})
        assert decided == render.Colour(sgr=True, palette=True)

    def test_a_plain_file_gets_neither(self):
        decided = render.Colour.decide(StringIO(), {})
        assert decided == render.Colour(sgr=False, palette=False)
