import argparse
import json
import logging
import os
import tempfile

from git import Repo
from git.exc import GitCommandError
from gitlab.v4.objects import ProjectMergeRequest

from ._common import (
    _ask,
    _get_gitlab_client_or_exit,
    acquire_mr_worktree,
    resolve_mr_from_args_or_branch,
)
from .aitools import run_agent
from .git_helpers import get_branch_diff, resolve_diff_range
from .gitlab_api import post_review_comment
from .models import (
    AgentRun,
    BranchWorktree,
    DiffRange,
    ReviewComment,
    ReviewCycleResult,
    ReviewFindings,
)
from .prompts import build_mr_fix_prompt, build_mr_review_prompt

logger = logging.getLogger(__name__)


def _read_comment_files(comments_dir: str) -> list[ReviewComment]:
    """Read and parse all JSON comment files written by AI."""
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
            # Strip the outer markdown code fence in case AI wrapped the JSON.
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


def _format_comments_for_fix(comments: list[ReviewComment]) -> str:
    """Format AI review findings into a text block suitable for the fix prompt."""
    lines = []
    for i, comment in enumerate(comments, 1):
        location = f"{comment.file}:{comment.line}" if comment.file else "(general)"
        lines.append(f"## Finding {i} [{comment.severity}] — {location}")
        if comment.context:
            lines.append("")
            lines.append("```")
            lines.append(comment.context)
            lines.append("```")
        lines.append("")
        lines.append(comment.body)
        lines.append("")
    return "\n".join(lines)


def post_all_review_comments(
    mr: ProjectMergeRequest, comments: list[ReviewComment]
) -> int:
    """Post every finding to the MR and return how many were posted."""
    for comment in comments:
        post_review_comment(mr, comment)
    print(f"Posted {len(comments)} comment(s) to MR !{mr.iid}.")
    return len(comments)


def _fix_from_comments(
    mr: ProjectMergeRequest,
    comments: list[ReviewComment],
    worktree: BranchWorktree,
    diff_range: DiffRange,
) -> AgentRun:
    """Run an AI agent to fix all review findings."""
    print(f"\nRunning fix agent for {len(comments)} finding(s)...")
    with tempfile.TemporaryDirectory(
        prefix=".loom_mrfix_", dir=worktree.path
    ) as context_dir:
        with open(
            os.path.join(context_dir, "review_comments.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(_format_comments_for_fix(comments))
        with open(os.path.join(context_dir, "branch.diff"), "w", encoding="utf-8") as f:
            f.write(
                get_branch_diff(
                    worktree.repo,
                    diff_range.ref,
                    mr.target_branch,
                    diff_range=diff_range,
                )
            )
        prompt = build_mr_fix_prompt(mr, context_dir)
        return run_agent(prompt, worktree, "mr-review-fix")


def collect_review_comments(
    mr: ProjectMergeRequest, worktree: BranchWorktree
) -> ReviewFindings:
    """Run the review agent over the MR branch and parse its findings."""
    with tempfile.TemporaryDirectory(
        prefix=".loom_mrreview_", dir=worktree.path
    ) as context_dir:
        comments_dir = os.path.join(context_dir, "comments")
        os.makedirs(comments_dir)

        diff_range = resolve_diff_range(worktree.repo, "HEAD", mr.target_branch)
        with open(os.path.join(context_dir, "branch.diff"), "w", encoding="utf-8") as f:
            f.write(
                get_branch_diff(
                    worktree.repo, "HEAD", mr.target_branch, diff_range=diff_range
                )
            )

        prompt = build_mr_review_prompt(mr, context_dir, comments_dir, diff_range)
        run = run_agent(prompt, worktree, "mr-review")

        comments = _read_comment_files(comments_dir)

    return ReviewFindings(comments=comments, diff_range=diff_range, run_ok=run.ok)


def run_review_cycle(
    mr: ProjectMergeRequest,
    worktree: BranchWorktree,
    post_comments: bool,
    fix: bool,
) -> ReviewCycleResult:
    """Review the MR, post the findings as inline comments, then fix them.

    The branch has to be checked out in `worktree`: the fix agent commits there.
    """
    findings = collect_review_comments(mr, worktree)
    if not findings.comments:
        return ReviewCycleResult(
            comments_found=0, comments_posted=0, fixed=False, commits_pushed=0
        )

    posted = post_all_review_comments(mr, findings.comments) if post_comments else 0
    if not fix:
        return ReviewCycleResult(
            comments_found=len(findings.comments),
            comments_posted=posted,
            fixed=False,
            commits_pushed=0,
        )

    _fix_from_comments(mr, findings.comments, worktree, findings.diff_range)
    try:
        ahead = list(worktree.repo.iter_commits(f"origin/{worktree.branch}..HEAD"))
    except GitCommandError:
        ahead = []
    if ahead:
        worktree.repo.git.push("origin", worktree.branch)
        print(f"Pushed {len(ahead)} review-fix commit(s) to {worktree.branch}")

    return ReviewCycleResult(
        comments_found=len(findings.comments),
        comments_posted=posted,
        fixed=True,
        commits_pushed=len(ahead),
    )


def cmd_mr_review(args: argparse.Namespace) -> None:
    """Run a multi-agent AI review of the current MR and post findings as comments."""
    repo = Repo(os.getcwd())
    gl = _get_gitlab_client_or_exit()
    mr = resolve_mr_from_args_or_branch(gl, args, repo)
    worktree = acquire_mr_worktree(mr, repo)
    print(f"Worktree: {worktree.path}")

    findings = collect_review_comments(mr, worktree)

    if not findings.comments:
        if not findings.run_ok:
            logger.warning(
                "The review agent did not complete, so it found nothing to report"
            )
            return
        print(f"\nReview complete. No issues found in MR !{mr.iid}.")
        if not args.fix:
            answer = _ask(f"Approve MR !{mr.iid}? [Y/n]: ")
            if answer in ("", "y"):
                mr.approve()
                print(f"Approved MR !{mr.iid}.")
        return

    print(f"\nFound {len(findings.comments)} review comment(s) for MR !{mr.iid}.")
    if args.fix:
        _fix_from_comments(mr, findings.comments, worktree, findings.diff_range)
    else:
        _review_comments_interactively(mr, findings.comments)
