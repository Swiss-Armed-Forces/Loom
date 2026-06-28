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
from .gitlab_api import find_open_mr_for_branch, get_gitlab_client, update_mr
from .models import MRContext

logger = logging.getLogger(__name__)


def _ask(prompt: str) -> str:
    """Prompt the user for input, or auto-accept in --auto mode."""
    if config.AUTO_MODE:
        print(f"{prompt}y (auto)")
        return "y"
    return input(prompt).strip().lower()


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
