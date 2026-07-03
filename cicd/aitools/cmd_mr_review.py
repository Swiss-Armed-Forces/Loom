import argparse
import json
import logging
import os
import tempfile

from git import Repo
from gitlab.v4.objects import ProjectMergeRequest

from ._common import _ask, _get_gitlab_client_or_exit, resolve_mr_from_args_or_branch
from .claude import run_claude_agentic
from .git_helpers import get_branch_diff
from .gitlab_api import post_review_comment
from .models import ReviewComment
from .prompts import build_mr_review_prompt

logger = logging.getLogger(__name__)


def _read_comment_files(comments_dir: str) -> list[ReviewComment]:
    """Read and parse all JSON comment files written by Claude."""
    if not os.path.isdir(comments_dir):
        logger.warning("Comments directory not found: %s", comments_dir)
        return []

    comments: list[ReviewComment] = []
    for filename in sorted(os.listdir(comments_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(comments_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read().strip()
            # Strip the outer markdown code fence in case Claude wrapped the JSON.
            # Only the first and last lines are removed to avoid corrupting inner
            # fences that appear inside JSON string values.
            if content.startswith("```"):
                lines = content.splitlines()
                content = "\n".join(lines[1:-1]).strip()
            data = json.loads(content)
            comments.append(
                ReviewComment(
                    file=data.get("file"),
                    line=int(data["line"]) if data.get("line") is not None else None,
                    severity=data.get("severity", "Low"),
                    body=data.get("body", ""),
                    context=data.get("context"),
                )
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to parse comment file %s: %s", filename, e)

    return comments


def _print_comment(i: int, total: int, comment: ReviewComment) -> None:
    """Print a single review comment with its context snippet."""
    location = f"{comment.file}:{comment.line}" if comment.file else "(general comment)"
    print(f"\n{'─' * 60}")
    print(f"[{i}/{total}] {comment.severity} — {location}")
    if comment.context:
        print()
        for line in comment.context.splitlines():
            print(f"  {line}")
    print()
    print(comment.body)


def _review_comments_interactively(
    mr: ProjectMergeRequest, comments: list[ReviewComment]
) -> None:
    """Show each comment with context and ask individually whether to post it."""
    posted = 0
    for i, comment in enumerate(comments, 1):
        _print_comment(i, len(comments), comment)
        print()
        answer = _ask("Post this comment? [Y/n]: ")
        if answer in ("", "y"):
            post_review_comment(mr, comment)
            posted += 1
            logger.info("Posted comment %d/%d", i, len(comments))
        else:
            logger.info("Skipped comment %d/%d", i, len(comments))

    print(f"\nPosted {posted}/{len(comments)} comment(s) to MR !{mr.iid}.")


def _resolve_branch_ref(mr: ProjectMergeRequest, repo: Repo) -> str:
    """Return the git ref to use for diffing the MR branch.

    If the MR's source branch is currently checked out, uses HEAD. Otherwise fetches the
    remote branch and returns its origin/ ref so the review works without requiring a
    local checkout.
    """
    source_branch = mr.source_branch
    try:
        if repo.active_branch.name == source_branch:
            return "HEAD"
    except TypeError:
        pass  # detached HEAD state
    logger.info("MR branch %r not checked out — fetching from origin", source_branch)
    repo.git.fetch("origin", source_branch)
    return f"origin/{source_branch}"


def cmd_mr_review(args: argparse.Namespace) -> None:
    """Run a multi-agent AI review of the current MR and post findings as comments."""
    repo = Repo(os.getcwd())
    gl = _get_gitlab_client_or_exit()
    mr = resolve_mr_from_args_or_branch(gl, args, repo)
    branch_ref = _resolve_branch_ref(mr, repo)

    with tempfile.TemporaryDirectory(
        prefix=".loom_mrreview_", dir=repo.working_dir
    ) as context_dir:
        comments_dir = os.path.join(context_dir, "comments")
        os.makedirs(comments_dir)

        with open(os.path.join(context_dir, "branch.diff"), "w", encoding="utf-8") as f:
            f.write(get_branch_diff(repo, branch_ref))

        prompt = build_mr_review_prompt(mr, context_dir, comments_dir, branch_ref)
        run_claude_agentic(prompt, repo)

        comments = _read_comment_files(comments_dir)

    if not comments:
        print(f"\nReview complete. No issues found in MR !{mr.iid}.")
        answer = _ask(f"Approve MR !{mr.iid}? [Y/n]: ")
        if answer in ("", "y"):
            mr.approve()
            print(f"Approved MR !{mr.iid}.")
        return

    print(f"\nFound {len(comments)} review comment(s) for MR !{mr.iid}.")
    _review_comments_interactively(mr, comments)
