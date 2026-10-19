"""`loom-issue-fragment`, which four units write the screen's lower blocks through."""

from banner_text import visible

from loom_banner.fragment import main


def written(tmp_path, *argv):
    """Every file the run left behind, which is none when it had nothing to say."""
    assert main([*argv, "--dir", str(tmp_path)]) == 0
    return sorted(tmp_path.iterdir())


def fragment(tmp_path, *argv):
    """The one fragment the run wrote."""
    files = written(tmp_path, *argv)
    assert len(files) == 1, files
    return files[0]


class TestPublishing:
    def test_the_name_is_the_position(self, tmp_path):
        """Agetty reads the directory in filename order, so the number in the name is
        where the block lands on screen."""
        path = fragment(tmp_path, "60-loom-network", "--warn", "loom0 does not exist.")
        assert path.name == "60-loom-network.issue"

    def test_nothing_to_say_writes_nothing(self, tmp_path):
        """An empty file would still cost the screen a blank row."""
        assert written(tmp_path, "61-loom-wifi") == []

    def test_no_half_written_file_is_left_behind(self, tmp_path):
        """A getty respawning mid-write must never paint half a message."""
        files = written(tmp_path, "60-loom-network", "--warn", "loom0 does not exist.")
        assert [path.name for path in files] == ["60-loom-network.issue"]

    def test_it_is_readable_by_the_getty(self, tmp_path):
        path = fragment(tmp_path, "60-loom-network", "--warn", "x")
        assert oct(path.stat().st_mode)[-3:] == "644"

    def test_rewriting_replaces_rather_than_appends(self, tmp_path):
        fragment(tmp_path, "61-loom-wifi", "--warn", "first")
        path = fragment(tmp_path, "61-loom-wifi", "--warn", "second")
        assert "first" not in path.read_text()
        assert "second" in path.read_text()


class TestWhatItSays:
    def test_a_problem_is_findable_and_red(self, tmp_path):
        path = fragment(
            tmp_path,
            "60-loom-network",
            "--warn",
            "loom0 does not exist -- no address, no DHCP, no *.loom.",
            "--warn",
            "No wired interface was found to claim.",
        )
        content = path.read_text()
        assert "── Problem ─" in visible(content)
        assert "\x1b[31m" in content
        # Both lines, in the order the unit gave them.
        assert visible(content).index("does not exist") < visible(content).index(
            "No wired interface"
        )

    def test_a_notice_is_not_dressed_as_a_problem(self, tmp_path):
        """A port claimed automatically is worth knowing, not wrong.

        Rendering it in red would make a working box look broken.
        """
        path = fragment(
            tmp_path,
            "60-loom-network",
            "--note",
            "loom0 is enp1s0, claimed automatically:",
        )
        content = path.read_text()
        assert "── Notice ─" in visible(content)
        assert "Problem" not in visible(content)
        assert "\x1b[31m" not in content

    def test_a_danger_block_carries_no_rule(self, tmp_path):
        """It is the loudest thing on the screen and needs no label to be found."""
        path = fragment(tmp_path, "90-loom-debug", "--bar", "DEBUG IMAGE")
        assert "Problem" not in visible(path.read_text())
        assert "\x1b[1;37;41m" in path.read_text()

    def test_the_screen_gets_colour_and_the_journal_does_not(self, tmp_path, capsys):
        """Every unit logs what it wrote, and SGR escapes in journalctl help nobody."""
        path = fragment(tmp_path, "60-loom-network", "--warn", "loom0 does not exist.")
        logged = capsys.readouterr().out
        assert "\x1b[" in path.read_text()
        assert "\x1b[" not in logged
        assert "loom0 does not exist." in logged

    def test_no_backslash_reaches_the_screen(self, tmp_path):
        path = fragment(tmp_path, "60-loom-network", "--warn", "a path, not a C:/one")
        assert "\\" not in path.read_text()
