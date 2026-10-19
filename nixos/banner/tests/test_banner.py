"""The whole screen, assembled the way `loom-info` assembles it.

The sections and the primitives are asserted on their own elsewhere; what is left here
is the seams between them, which is where a banner goes wrong in ways that are invisible
until somebody looks at a monitor: a line continuing the one the escape before it was
written on, a block broken up by blank rows, a row past the margin.
"""

from banner_text import WARNINGS, columns, visible

from loom_banner.__main__ import main


def paint(box, capsys, *extra):
    assert main([*box, *extra]) == 0
    return capsys.readouterr().out


class TestTheWholeScreen:
    def test_nothing_agetty_would_eat(self, box, capsys):
        assert "\\" not in paint(box, capsys)

    def test_nothing_past_the_margin(self, box, capsys):
        """The narrowest console in play is the 80-column getty a --vm-serial box
        carries, and what does not fit does not wrap -- it scrolls the mark away."""
        painted = paint(box, capsys)
        too_wide = [line for line in painted.split("\n") if columns(line) > 80]
        assert too_wide == []

    def test_the_text_starts_on_its_own_row(self, box, capsys):
        """The mark's colour is closed with an escape, and an unterminated escape line
        leaves the first row of text continuing it."""
        rows = visible(paint(box, capsys)).split("\n")
        assert "  Loom appliance 1.5.0-rc6 -- NVIDIA DGX Spark" in rows

    def test_every_section_is_announced(self, box, capsys):
        painted = visible(paint(box, capsys))
        for title in ("Connect", "Write these down", "This box"):
            assert f"── {title} ─" in painted

    def test_the_mark_is_drawn_from_its_own_command(self, box, capsys):
        assert "XXXX  XXXX" in paint(box, capsys)

    def test_a_generator_that_cannot_be_reached_costs_only_itself(
        self, tmp_path, capsys
    ):
        """A missing mark is a worse screen; a traceback where the login prompt should
        be is no screen at all."""
        painted = paint(
            ["--tag", "1.5.0", "--platform", "x", "--eyes", str(tmp_path / "gone")],
            capsys,
        )
        assert "Loom appliance 1.5.0 -- x" in visible(painted)


class TestTheDangerBlock:
    def test_it_is_one_block(self, box, capsys):
        """Blank rows between the lines would break the rectangle into stripes."""
        rows = visible(paint(box, capsys)).rstrip("\n").split("\n")
        first = next(i for i, row in enumerate(rows) if WARNINGS[0] in row)
        last = next(i for i, row in enumerate(rows) if WARNINGS[1] in row)
        assert [row for row in rows[first:last] if not row.strip()] == []

    def test_it_is_last(self, box, capsys):
        """The issue is written straight to the VT with no paging, so a banner taller
        than its console loses its first rows -- and the tail is the only position that
        cannot scroll away."""
        rows = visible(paint(box, capsys)).rstrip("\n").split("\n")
        after = rows[max(i for i, row in enumerate(rows) if WARNINGS[1] in row) + 1 :]
        assert [row for row in after if row.strip()] == []

    def test_the_login_screen_leaves_it_to_its_own_fragment(self, box, capsys):
        """On the screen it is written as a numbered fragment so that it sorts below
        every other unit's block, which a section of this file could not do."""
        painted = paint(box, capsys, "--for-issue")
        assert WARNINGS[0] not in painted
        # Everything else is still there.
        assert "Write these down" in visible(painted)
