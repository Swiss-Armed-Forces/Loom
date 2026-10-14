"""Unit tests for rendering an MR description from the repository's MR template.

The description an MR is born with decides whether the MR closes its issue, so what
lands under the issue reference heading is behaviour worth pinning down - including the
cases where the template is missing or no longer carries that heading.
"""

import os

import pytest
from git import Repo

from aitools.git_helpers import build_initial_mr_description, load_mr_template

REPO_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".gitlab",
    "merge_request_templates",
    "Default.md",
)


@pytest.fixture(name="repo_template")
def fixture_repo_template() -> str:
    """The MR template this repository actually ships, read from disk."""
    with open(REPO_TEMPLATE_PATH, encoding="utf-8") as f:
        return f.read()


class TestLoadMrTemplate:
    def test_expansion_variable_is_stripped(self, tmp_path):
        """A %{...} variable expands in the web UI only, and is literal everywhere
        else."""
        repo = Repo.init(tmp_path)
        template_dir = tmp_path / ".gitlab" / "merge_request_templates"
        template_dir.mkdir(parents=True)
        (template_dir / "Default.md").write_text(
            "# Summary\n\n%{first_multiline_commit_description}\n\n## Issue Reference\n",
            encoding="utf-8",
        )

        template = load_mr_template(repo)

        assert "%{" not in template
        assert "# Summary" in template
        assert "## Issue Reference" in template

    def test_missing_template_is_not_an_error(self, tmp_path):
        """A checkout without the template still has to produce a usable description."""
        repo = Repo.init(tmp_path)

        assert load_mr_template(repo) == ""


class TestBuildInitialMrDescription:
    def test_issue_reference_lands_under_its_own_heading(self, repo_template):
        description = build_initial_mr_description(repo_template, 42)

        lines = description.splitlines()
        heading_index = next(
            i
            for i, line in enumerate(lines)
            if line.startswith("## ") and "Issue Reference" in line
        )
        assert "Closes #42" in lines[heading_index + 1 :]
        assert "Closes #42" not in lines[:heading_index]

    def test_hint_comments_do_not_reach_the_description(self, repo_template):
        """The template's "<!-- Closes #<issue-number> -->" prompts a human, not
        GitLab."""
        description = build_initial_mr_description(repo_template, 42)

        assert "<!--" not in description
        assert "#<issue-number>" not in description

    def test_removed_lines_leave_no_blank_run_behind(self, repo_template):
        """The stripped variable and hint comment each sat between blank lines."""
        description = build_initial_mr_description(repo_template, 42)

        assert "\n\n\n" not in description

    def test_empty_template_still_closes_the_issue(self):
        """load_mr_template returns "" for a missing file or a bare repo."""
        assert build_initial_mr_description("", 42) == "Closes #42"

    def test_template_without_the_heading_still_closes_the_issue(self):
        description = build_initial_mr_description("# 📌 Summary\n", 42)

        assert description.startswith("# 📌 Summary")
        assert "Closes #42" in description
