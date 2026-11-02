"""Unit tests for what the MR title/description prompt tells the AI to produce.

The MR title and description become the title and message of the squashed commit on the
target branch, so two rules are not cosmetic: the title has to be a conventional commit
subject, and the description has to carry the template's headings and nothing else. Both
are gotten wrong by default often enough to be worth pinning, here and in the template
the prompt embeds.
"""

import os
import re

import pytest

from aitools.prompts import build_mr_update_prompt

REPO_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".gitlab",
    "merge_request_templates",
    "Default.md",
)

# A comment that opens and closes on one line. build_initial_mr_description drops the
# template's hints with a per-line regex, so only this shape is ever removed.
SINGLE_LINE_COMMENT = re.compile(r"^[ \t]*<!--.*-->[ \t]*$")


@pytest.fixture(name="repo_template")
def fixture_repo_template() -> str:
    """The MR template this repository actually ships, read from disk."""
    with open(REPO_TEMPLATE_PATH, encoding="utf-8") as f:
        return f.read()


class TestTitleConvention:
    """The title becomes a commit subject, so it must be told to look like one."""

    def test_conventional_commit_format_is_required(self) -> None:
        prompt = build_mr_update_prompt("")

        assert "conventional commit format (type(scope): description)" in prompt
        assert "72 characters" in prompt

    def test_a_worked_example_is_given(self) -> None:
        """A format name on its own still produces sentence-style titles."""
        prompt = build_mr_update_prompt("")

        assert "feat(api):" in prompt

    def test_sentence_style_titles_are_called_out_as_wrong(self) -> None:
        prompt = build_mr_update_prompt("")

        assert "sentence-style title" in prompt.lower()


class TestNoInventedSections:
    """Anything beyond the template's headings becomes permanent commit message."""

    def test_extra_sections_are_forbidden(self, repo_template: str) -> None:
        prompt = build_mr_update_prompt(repo_template)

        assert "no heading the template does not" in prompt
        assert "Do not add sections of your own" in prompt

    def test_the_section_claude_kept_adding_is_named(self, repo_template: str) -> None:
        """The generic rule alone is not enough; the offending section has to be
        named."""
        prompt = build_mr_update_prompt(repo_template)

        assert "Notes for review" in prompt

    def test_template_comments_are_not_to_be_echoed(self, repo_template: str) -> None:
        """The template is embedded verbatim, hint comments included."""
        prompt = build_mr_update_prompt(repo_template)

        assert "HTML comment" in prompt

    def test_rules_are_absent_without_a_template(self) -> None:
        """They are part of the template instruction, which is skipped when empty."""
        prompt = build_mr_update_prompt("")

        assert "Do not add sections of your own" not in prompt


class TestSquashCommitIsExplained:
    """The reason, so the rules are not read as style preferences."""

    def test_prompt_says_the_output_becomes_the_squashed_commit(self) -> None:
        prompt = build_mr_update_prompt("")

        assert "squashed commit" in prompt


class TestShippedTemplate:
    """The template is read by the web UI and embedded in this prompt."""

    def test_every_comment_is_a_single_line(self, repo_template: str) -> None:
        """A block comment would survive into the description of a created MR.

        build_initial_mr_description strips hints with a per-line regex, so a comment
        spanning several lines is kept and lands in the MR body — and from there in the
        squashed commit message.
        """
        for line in repo_template.splitlines():
            if "<!--" in line or "-->" in line:
                assert SINGLE_LINE_COMMENT.match(
                    line
                ), f"not a one-line comment: {line}"

    def test_template_states_the_title_convention(self, repo_template: str) -> None:
        """Someone opening an MR in the web UI never sees CLAUDE.md."""
        assert "conventional commit" in repo_template.lower()

    def test_template_forbids_extra_sections(self, repo_template: str) -> None:
        assert "Do not add sections of your own" in repo_template

    def test_template_keeps_its_two_headings(self, repo_template: str) -> None:
        assert "# 📌 Summary" in repo_template
        assert "## 🔗 Issue Reference" in repo_template
