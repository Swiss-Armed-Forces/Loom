import argparse
import logging
import os
import sys
import tempfile

from git import Repo
from git.exc import GitCommandError
from gitlab.v4.objects import Project, ProjectIssue

from ._common import _ask, _get_gitlab_client_or_exit, _maybe_update_mr_description
from .claude import run_claude_agentic
from .gitlab_api import (
    create_branch_and_mr_for_issue,
    fetch_issue_by_ref,
    fetch_milestone_by_ref,
    fetch_open_issues_for_milestone,
    find_open_mr_for_issue,
    get_project,
    parse_issue_url_or_id,
    parse_milestone_url_or_id,
)
from .models import IssueBranchResult
from .prompts import build_implement_prompt, build_milestone_implement_prompt

logger = logging.getLogger(__name__)


def _checkout_issue_branch(
    project: Project, issue: ProjectIssue, repo: Repo
) -> IssueBranchResult:
    """Find or create an MR for the issue and check out its branch locally."""
    mr = find_open_mr_for_issue(project, issue)
    if mr:
        branch_name = mr.source_branch
        print(f"Found existing MR !{mr.iid} on branch {branch_name}")
    else:
        mr, branch_name = create_branch_and_mr_for_issue(project, issue)
        print(f"Created MR !{mr.iid} on branch {branch_name}")

    local_branches = [b.name for b in repo.branches]
    if branch_name in local_branches:
        repo.git.checkout(branch_name)
        repo.git.reset("--hard", f"origin/{branch_name}")
    else:
        repo.git.checkout("-b", branch_name, f"origin/{branch_name}")

    return IssueBranchResult(mr=mr, branch_name=branch_name)


def _implement_issue(project: Project, issue: ProjectIssue, repo: Repo) -> None:
    """Run the full implementation loop for a single issue."""
    print(f"\n=== Issue #{issue.iid}: {issue.title} ===")
    repo.git.fetch("origin")

    result = _checkout_issue_branch(project, issue, repo)

    with tempfile.TemporaryDirectory(
        prefix=".loom_milestone_implement_", dir=repo.working_dir
    ) as context_dir:
        with open(os.path.join(context_dir, "issue.md"), "w", encoding="utf-8") as f:
            f.write(f"# {issue.title}\n\n{issue.description or ''}")
        run_claude_agentic(build_milestone_implement_prompt(issue, context_dir), repo)

    try:
        ahead = list(repo.iter_commits(f"origin/{result.branch_name}..HEAD"))
    except GitCommandError:
        ahead = []

    if not ahead:
        print("No commits made — skipping push and MR update")
        return

    repo.git.push("--set-upstream", "origin", result.branch_name)
    _maybe_update_mr_description(result.mr, repo)


def cmd_implement(args: argparse.Namespace) -> None:
    """Implement a GitLab issue using Claude in agentic mode."""
    try:
        ref = parse_issue_url_or_id(args.issue_number)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    repo = Repo(os.getcwd())

    gl = _get_gitlab_client_or_exit()

    issue = fetch_issue_by_ref(gl, repo, ref)
    labels = ", ".join(issue.labels) if issue.labels else "(none)"

    print(f"\nIssue #{issue.iid}: {issue.title}")
    print(f"URL: {issue.web_url}")
    print(f"Labels: {labels}")
    print()

    answer = _ask("Proceed with implementation? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    with tempfile.TemporaryDirectory(
        prefix=".loom_implement_", dir=repo.working_dir
    ) as context_dir:
        with open(os.path.join(context_dir, "issue.md"), "w", encoding="utf-8") as f:
            f.write(f"# {issue.title}\n\n{issue.description or ''}")
        prompt = build_implement_prompt(issue, context_dir)
        run_claude_agentic(prompt, repo)


def cmd_milestone_implement(args: argparse.Namespace) -> None:
    """Implement all open issues in a GitLab milestone using Claude in agentic mode."""
    try:
        ref = parse_milestone_url_or_id(args.milestone)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    repo = Repo(os.getcwd())
    original_branch = repo.active_branch.name

    gl = _get_gitlab_client_or_exit()

    project = get_project(gl, repo)
    milestone = fetch_milestone_by_ref(gl, repo, ref)
    logger.info("Milestone: %s", milestone.title)

    issues = fetch_open_issues_for_milestone(project, milestone)
    if not issues:
        print("No open issues in milestone.")
        return

    print(f"\nOpen issues in milestone '{milestone.title}':")
    for issue in issues:
        print(f"  #{issue.iid}: {issue.title}")
    print()

    answer = _ask(f"Implement {len(issues)} issue(s)? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    try:
        for issue in issues:
            _implement_issue(project, issue, repo)
    finally:
        repo.git.checkout(original_branch)
        print(f"\nDone. Returned to branch {original_branch}")
