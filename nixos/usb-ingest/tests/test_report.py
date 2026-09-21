"""What the operator is told when something goes wrong.

The box has no remote access, so a reason that only reaches the journal reaches nobody:
the console session has no way to read one. These are about the line that does reach
them -- that it carries the reason, and that it stays a line.
"""

from loom_usb_ingest.report import REASON_LIMIT, condense


def test_the_failure_is_the_first_line() -> None:
    # mc follows its error with hints and kubectl with usage, and the operator needs
    # the sentence at the top of that, not the bottom of it.
    detail = (
        "mc: <ERROR> Unable to initialize new alias from the provided credentials.\n"
        'Get "https://s3.loom/probe-bucket-sign/": dial tcp: connection refused.\n'
    )

    assert condense(detail).startswith("mc: <ERROR> Unable to initialize")


def test_leading_blank_lines_are_not_the_message() -> None:
    assert condense("\n\n  the actual failure\n") == "the actual failure"


def test_a_long_reason_is_cut_to_something_a_terminal_can_hold() -> None:
    # `wall` writes to every terminal on the box and tmux's display-message is one
    # line over the status bar: a page of JSON would cost somebody the screen they
    # were working on. The whole thing is in the journal.
    condensed = condense("x" * (REASON_LIMIT * 3))

    assert len(condensed) == REASON_LIMIT
    assert condensed.endswith("...")


def test_nothing_to_report_reports_nothing() -> None:
    # A caller with a headline and no detail -- a device that is not a block device
    # -- gets the headline alone rather than a stray colon.
    assert condense("") == ""
    assert condense("   \n  \n") == ""
