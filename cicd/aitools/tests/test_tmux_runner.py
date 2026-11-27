"""Unit tests for reading strand state back out of tmux."""

from aitools.tmux_runner import parse_strand_statuses

LISTING = """issue-461 0
issue-462 1 0
issue-463 1 1
scratch 1 0
"""


class TestParseStrandStatuses:
    def test_dead_panes_report_how_their_command_exited(self):
        statuses = {
            status.issue_iid: status for status in parse_strand_statuses(LISTING)
        }

        assert set(statuses) == {461, 462, 463}
        assert statuses[461].dead is False
        assert statuses[462].dead is True
        assert statuses[462].exit_code == 0
        assert statuses[463].exit_code == 1
