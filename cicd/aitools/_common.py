import argparse
import logging
import sys

import gitlab
from git import Repo
from gitlab.v4.objects import ProjectMergeRequest

from . import config
from .claude import (
    generate_commit_message_via_claude,
    parse_commit_message,
)
from .git_helpers import get_branch_diff, load_mr_template
from .gitlab_api import (
    fetch_mr_by_ref,
    find_open_mr_for_branch,
    get_gitlab_client,
    parse_mr_url_or_id,
    update_mr,
)
from .models import MRContext

logger = logging.getLogger(__name__)


def checkout_mr_branch(mr: ProjectMergeRequest, repo: Repo) -> str:
    """Check out the MR's source branch locally and return the branch name."""
    branch_name = mr.source_branch
    repo.git.fetch("origin")
    local_branches = [b.name for b in repo.branches]
    if branch_name in local_branches:
        repo.git.checkout(branch_name)
        repo.git.reset("--hard", f"origin/{branch_name}")
    else:
        repo.git.checkout("-b", branch_name, f"origin/{branch_name}")
    return branch_name


def _ask(prompt: str) -> str:
    """Prompt the user for input, or auto-accept in --auto mode."""
    if config.AUTO_MODE:
        print(f"{prompt}y (auto)")
        return "y"
    return input(prompt).strip().lower()


def resolve_mr_from_args_or_branch(
    gl: gitlab.Gitlab, args: argparse.Namespace, repo: Repo
) -> ProjectMergeRequest:
    """Resolve the target MR: explicit URL/IID from args, or the MR for the current
    branch.

    Handles detached HEAD state with a clear error message directing the user to pass
    the MR reference explicitly.
    """
    if args.mr:
        try:
            ref = parse_mr_url_or_id(args.mr)
        except ValueError as e:
            logger.error("%s", e)
            sys.exit(1)
        return fetch_mr_by_ref(gl, repo, ref)
    if repo.head.is_detached:
        logger.error(
            "Detached HEAD: cannot determine current branch. Pass --mr explicitly."
        )
        sys.exit(1)
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)
    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)
    logger.info("Found MR !%s: %s", mr.iid, mr.title)
    return mr


def _get_gitlab_client_or_exit() -> gitlab.Gitlab:
    """Return a GitLab client or exit with an error message."""
    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)
    return gl


def _get_mr_for_current_branch(repo: Repo) -> ProjectMergeRequest:
    """Return the open MR for the current branch, or exit with an error."""
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)
    gl = _get_gitlab_client_or_exit()
    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)
    logger.info("Found MR !%s: %s", mr.iid, mr.title)
    return mr


def _maybe_update_mr_description(mr: ProjectMergeRequest, repo: Repo) -> None:
    """Generate a new MR title/description via Claude and optionally apply it."""
    diff = get_branch_diff(repo)
    mr_template = load_mr_template(repo)
    message = generate_commit_message_via_claude(
        diff,
        mr_template,
        repo,
        MRContext(title=mr.title, description=mr.description or ""),
    )
    if not message:
        logger.warning("Could not generate MR description for !%s — skipping", mr.iid)
        return
    parsed = parse_commit_message(message)
    print("\n--- MR Preview ---")
    print(f"Title: {parsed.title}\n")
    print(f"Description:\n{parsed.body}")
    print("--- End Preview ---\n")
    answer = _ask(f"Update MR !{mr.iid} description? [Y/n]: ")
    if answer in ("", "y"):
        update_mr(mr, parsed.title, parsed.body)
        logger.info("Updated MR !%s", mr.iid)
