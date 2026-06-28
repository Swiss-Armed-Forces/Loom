import argparse
import logging
import os
import sys

from git import Repo

from ._common import _ask, _get_mr_for_current_branch
from .claude import (
    generate_commit_message_via_claude,
    is_claude_cli_installed,
    parse_commit_message,
)
from .git_helpers import get_branch_diff, load_mr_template
from .gitlab_api import update_mr
from .models import MRContext

logger = logging.getLogger(__name__)


def cmd_mr_update(args: argparse.Namespace) -> None:
    """Update GitLab MR title and description using Claude."""
    user_instructions = " ".join(args.instructions) if args.instructions else ""

    if user_instructions:
        logger.info("User instructions: %s", user_instructions)

    repo = Repo(os.getcwd())
    mr = _get_mr_for_current_branch(repo)

    diff = get_branch_diff(repo)
    if not diff:
        logger.info("No changes on this branch compared to its merge base.")
        return

    mr_template = load_mr_template(repo)

    if not is_claude_cli_installed():
        logger.error("Claude CLI not installed.")
        sys.exit(1)

    message = generate_commit_message_via_claude(
        diff,
        mr_template,
        repo,
        MRContext(
            title=mr.title or "",
            description=mr.description or "",
            user_instructions=user_instructions,
        ),
    )
    if not message:
        logger.error("Failed to generate commit message via Claude.")
        sys.exit(1)

    parsed = parse_commit_message(message)

    print("\n--- Preview ---")
    print(f"Title: {parsed.title}\n")
    print(f"Description:\n{parsed.body}")
    print("--- End Preview ---\n")

    answer = _ask(f"Update MR !{mr.iid} with the above? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    update_mr(mr, parsed.title, parsed.body)
    logger.info("Updated MR !%s", mr.iid)
