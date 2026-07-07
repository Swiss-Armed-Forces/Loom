import argparse
import logging
import os
import sys
import tempfile

from git import Repo
from gitlab.v4.objects import ProjectMergeRequest, ProjectMergeRequestDiscussion

from ._common import (
    _ask,
    _get_gitlab_client_or_exit,
    checkout_mr_branch,
    resolve_mr_from_args_or_branch,
)
from .claude import generate_discussion_reply, run_claude_agentic
from .git_helpers import get_branch_diff
from .gitlab_api import (
    extract_discussion_location,
    fetch_unresolved_discussions,
    format_discussions_for_prompt,
    post_discussion_reply,
)
from .models import DiscussionReply
from .prompts import build_mr_fix_prompt

logger = logging.getLogger(__name__)


def _print_discussion_previews(
    discussions: list[ProjectMergeRequestDiscussion],
) -> None:
    """Print a one-line summary of each unresolved discussion."""
    for discussion in discussions:
        notes = discussion.attributes.get("notes", [])
        if not notes:
            continue
        first_note = notes[0]
        author = first_note.get("author", {}).get("username", "unknown")
        body = first_note.get("body", "")
        position = first_note.get("position") or {}
        new_path = position.get("new_path", "(general comment)")
        print(f"  @{author} on {new_path}: {body[:80]}")


def _generate_and_post_replies(
    mr: ProjectMergeRequest,
    discussions: list[ProjectMergeRequestDiscussion],
    updated_diff: str,
    repo: Repo,
) -> None:
    """Generate Claude replies for all discussions, preview them, then post."""
    replies: list[DiscussionReply] = []
    for i, discussion in enumerate(discussions, 1):
        location = extract_discussion_location(discussion)
        logger.info("Generating reply %d/%d for %s...", i, len(discussions), location)
        reply = generate_discussion_reply(discussion, updated_diff, repo)
        if reply:
            replies.append(
                DiscussionReply(discussion=discussion, location=location, reply=reply)
            )
        else:
            logger.warning("Could not generate reply for %s — skipping", location)

    if not replies:
        logger.warning("No replies were generated.")
        return

    print("\n--- Reply Preview ---")
    for dr in replies:
        print(f"\n[{dr.location}]\n{dr.reply}")
    print("--- End Preview ---\n")

    answer = _ask(f"Post {len(replies)} reply/replies to MR !{mr.iid}? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    for dr in replies:
        post_discussion_reply(dr.discussion, dr.reply)
        logger.info("Posted reply for %s", dr.location)

    print(f"Posted {len(replies)} reply/replies.")


def cmd_mr_fix(args: argparse.Namespace) -> None:
    """Address unresolved MR review comments using Claude in agentic mode."""
    repo = Repo(os.getcwd())
    gl = _get_gitlab_client_or_exit()
    mr = resolve_mr_from_args_or_branch(gl, args, repo)

    source_branch = mr.source_branch
    try:
        on_mr_branch = repo.active_branch.name == source_branch
    except TypeError:
        on_mr_branch = False  # detached HEAD

    if not on_mr_branch:
        if repo.is_dirty(untracked_files=True):
            logger.error(
                "You have uncommitted changes. Please commit or stash them"
                " before switching to branch %r.",
                source_branch,
            )
            sys.exit(1)
        checkout_mr_branch(mr, repo)

    discussions = fetch_unresolved_discussions(mr)
    if not discussions:
        logger.info("No unresolved review threads found. Nothing to do.")
        return

    print(f"\nFound {len(discussions)} unresolved thread(s) in MR !{mr.iid}:\n")
    _print_discussion_previews(discussions)
    print()

    with tempfile.TemporaryDirectory(
        prefix=".loom_mrfix_", dir=repo.working_dir
    ) as context_dir:
        with open(
            os.path.join(context_dir, "review_comments.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(format_discussions_for_prompt(discussions))
        with open(os.path.join(context_dir, "branch.diff"), "w", encoding="utf-8") as f:
            f.write(get_branch_diff(repo))
        prompt = build_mr_fix_prompt(mr, context_dir)
        run_claude_agentic(prompt, repo)

    updated_diff = get_branch_diff(repo)
    _generate_and_post_replies(mr, discussions, updated_diff, repo)
