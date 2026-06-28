import argparse
import logging
import os
import sys
import tempfile

from git import Repo

from ._common import _ask, _get_gitlab_client_or_exit
from .claude import run_claude_agentic
from .gitlab_api import (
    fetch_issue_by_ref,
    fetch_issue_notes,
    format_issue_notes_for_context,
    parse_issue_url_or_id,
    update_issue_description,
)
from .prompts import build_issue_update_prompt

logger = logging.getLogger(__name__)


def cmd_issue_update(args: argparse.Namespace) -> None:
    """Update a GitLab issue description interactively using Claude."""
    repo = Repo(os.getcwd())

    try:
        issue_ref = parse_issue_url_or_id(args.issue)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    gl = _get_gitlab_client_or_exit()

    issue = fetch_issue_by_ref(gl, repo, issue_ref)

    print(f"\nIssue #{issue.iid}: {issue.title}")
    print(f"URL: {issue.web_url}\n")

    notes = fetch_issue_notes(issue)
    logger.info("Fetched %d comment(s)", len(notes))

    with tempfile.TemporaryDirectory(
        prefix=".loom_issue_update_", dir=repo.working_dir
    ) as context_dir:
        with open(os.path.join(context_dir, "issue.md"), "w", encoding="utf-8") as f:
            f.write(f"# {issue.title}\n\n{issue.description or ''}")
        with open(os.path.join(context_dir, "comments.md"), "w", encoding="utf-8") as f:
            f.write(format_issue_notes_for_context(notes))
        proposed_path = os.path.join(context_dir, "proposed_description.md")
        with open(proposed_path, "w", encoding="utf-8") as f:
            f.write(issue.description or "")

        prompt = build_issue_update_prompt(issue, context_dir)
        run_claude_agentic(prompt, repo)

        with open(proposed_path, encoding="utf-8") as f:
            new_description = f.read().strip()

    if not new_description:
        logger.error("proposed_description.md is empty — aborting.")
        sys.exit(1)

    print("\n--- Proposed Description ---")
    print(new_description)
    print("--- End ---\n")

    answer = _ask(f"Update issue #{issue.iid} with the above description? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    update_issue_description(issue, new_description)
    logger.info("Updated issue #%s", issue.iid)
    print(f"Issue #{issue.iid} updated.")
