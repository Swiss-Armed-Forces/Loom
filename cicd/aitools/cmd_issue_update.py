import argparse
import logging
import os
import sys
import tempfile

from git import Repo
from gitlab.v4.objects import ProjectIssue, ProjectIssueDiscussion

from ._common import _ask, _get_gitlab_client_or_exit
from .claude import generate_issue_note_reply, run_claude_agentic
from .gitlab_api import (
    fetch_issue_by_ref,
    fetch_issue_discussions,
    fetch_issue_notes,
    format_issue_notes_for_context,
    parse_issue_url_or_id,
    post_issue_discussion_reply,
    update_issue_description,
)
from .models import IssueNoteReply
from .prompts import build_issue_update_prompt

logger = logging.getLogger(__name__)


def _get_discussion_author(discussion: ProjectIssueDiscussion) -> str:
    notes = discussion.attributes.get("notes", [])
    if not notes:
        return "unknown"
    return notes[0].get("author", {}).get("username", "unknown")


def _generate_and_post_note_replies(
    issue: ProjectIssue,
    discussions: list[ProjectIssueDiscussion],
    old_description: str,
    new_description: str,
    repo: Repo,
) -> None:
    """Generate Claude replies for all issue comment threads, preview them, then
    post."""
    replies: list[IssueNoteReply] = []
    for i, discussion in enumerate(discussions, 1):
        author = _get_discussion_author(discussion)
        logger.info(
            "Generating reply %d/%d for comment by @%s...", i, len(discussions), author
        )
        reply = generate_issue_note_reply(
            discussion, old_description, new_description, repo
        )
        if reply:
            replies.append(IssueNoteReply(discussion=discussion, reply=reply))
        else:
            logger.warning(
                "Could not generate reply for comment by @%s — skipping", author
            )

    if not replies:
        logger.warning("No replies were generated.")
        return

    print("\n--- Reply Preview ---")
    for nr in replies:
        author = _get_discussion_author(nr.discussion)
        print(f"\n[@{author}]\n{nr.reply}")
    print("--- End Preview ---\n")

    answer = _ask(f"Post {len(replies)} reply/replies to issue #{issue.iid}? [Y/n]: ")
    if answer not in ("", "y"):
        print("Aborted.")
        return

    for nr in replies:
        post_issue_discussion_reply(nr.discussion, nr.reply)
        logger.info("Posted reply for discussion %s", nr.discussion.id)

    print(f"Posted {len(replies)} reply/replies.")


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

    old_description = issue.description or ""

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

    discussions = fetch_issue_discussions(issue)
    if discussions:
        _generate_and_post_note_replies(
            issue, discussions, old_description, new_description, repo
        )
