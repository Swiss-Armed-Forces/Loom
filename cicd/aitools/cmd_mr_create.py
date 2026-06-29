import argparse
import logging
import os
import sys

from git import Repo
from git.exc import GitCommandError

from ._common import _ask, _get_gitlab_client_or_exit
from .claude import (
    generate_commit_message_via_claude,
    is_claude_cli_installed,
    parse_commit_message,
    run_claude_agentic,
)
from .config import EXCLUDED_PATHSPECS, MAX_DIFF_CHARS
from .git_helpers import load_mr_template
from .gitlab_api import get_project
from .prompts import build_mr_create_commit_prompt

logger = logging.getLogger(__name__)


def _checkout_branch(repo: Repo, branch_name: str) -> None:
    """Create and check out branch_name, or switch to it if it already exists."""
    try:
        repo.git.checkout("-b", branch_name)
    except GitCommandError:
        try:
            repo.git.checkout(branch_name)
        except GitCommandError as e:
            logger.error("Failed to check out branch %r: %s", branch_name, e)
            sys.exit(1)


def cmd_mr_create(args: argparse.Namespace) -> None:
    """Create a new branch, commit all changes, push, and open a draft MR."""
    repo = Repo(os.getcwd())

    if not repo.is_dirty(untracked_files=True):
        logger.error("No changes to commit.")
        sys.exit(1)

    if not is_claude_cli_installed():
        logger.error("Claude CLI not installed.")
        sys.exit(1)

    gl = _get_gitlab_client_or_exit()
    project = get_project(gl, repo)

    branch_name = f"{args.type}/{args.name}"
    print(f"Creating branch: {branch_name}")

    _checkout_branch(repo, branch_name)

    repo.git.add("-A")

    stat = repo.git.diff("--staged", "--stat", "--", *EXCLUDED_PATHSPECS)
    diff = repo.git.diff("--staged", "--", *EXCLUDED_PATHSPECS)
    if not diff:
        diff = repo.git.diff("--staged")
        stat = repo.git.diff("--staged", "--stat")

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + (
            f"\n\n[Diff truncated at {MAX_DIFF_CHARS} characters."
            " See stat summary above for full file list.]"
        )

    staged_diff = (
        f"Changed files:\n{stat}\n\nDiff:\n{diff}" if stat else f"Diff:\n{diff}"
    )

    mr_template = load_mr_template(repo)
    message = generate_commit_message_via_claude(staged_diff, mr_template, repo)
    if not message:
        logger.error("Failed to generate commit message via Claude.")
        sys.exit(1)

    parsed = parse_commit_message(message)

    print("\n--- Preview ---")
    print(f"Commit / MR title: {parsed.title}\n")
    if parsed.body:
        print(f"MR description:\n{parsed.body}")
    print("--- End Preview ---\n")

    answer = _ask("Commit, push, and create MR? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    run_claude_agentic(build_mr_create_commit_prompt(parsed.title), repo)

    try:
        committed = list(repo.iter_commits("origin/main..HEAD"))
    except GitCommandError:
        committed = []

    if not committed:
        logger.error("No commit was made — aborting.")
        sys.exit(1)

    repo.git.push("--set-upstream", "origin", branch_name)

    mr = project.mergerequests.create(
        {
            "source_branch": branch_name,
            "target_branch": "main",
            "title": f"Draft: {parsed.title}",
            "description": parsed.body,
        }
    )
    print(f"\nCreated MR !{mr.iid}: {mr.title}")
    print(f"URL: {mr.web_url}")
