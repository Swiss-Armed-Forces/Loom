import argparse
import logging
import os
import sys
import tempfile

from git import Repo
from git.exc import GitCommandError

from ._common import _get_mr_for_current_branch, acquire_mr_worktree
from .aitools import is_ai_cli_installed, run_agent
from .models import BranchWorktree
from .prompts import build_merge_conflict_prompt

logger = logging.getLogger(__name__)


def _resolve_conflicts_and_commit(
    worktree: BranchWorktree, conflicting: list[str], target_branch: str
) -> None:
    """Have the agent resolve a conflicted merge, then commit what it left."""
    repo = worktree.repo
    with tempfile.TemporaryDirectory(
        prefix=".loom_mrupdate_", dir=worktree.path
    ) as ctx:
        with open(os.path.join(ctx, "conflicts.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(conflicting))
        run = run_agent(
            build_merge_conflict_prompt(
                worktree.branch, conflicting, ctx, target_branch
            ),
            worktree,
            "mr-update",
        )

    # The commit below runs with hooks disabled, so a file the agent left unmerged
    # would reach the branch carrying its conflict markers.
    unmerged = repo.git.diff("--name-only", "--diff-filter=U").splitlines()
    if unmerged:
        logger.error(
            "Still unmerged after the agent ran: %s. The merge is left in place to "
            "finish by hand (agent: %s, transcript: %s)",
            ", ".join(unmerged),
            run.error or "completed",
            run.transcript_path,
        )
        sys.exit(1)

    repo.git.add("-A")
    repo.git.commit(
        "--no-verify",
        "-m",
        f"chore: merge origin/{target_branch} into {worktree.branch}",
    )
    print("Resolved merge conflicts and committed.")


def cmd_mr_update(_args: argparse.Namespace) -> None:
    """Merge the MR's target branch into the current branch, resolve any conflicts, and
    push."""
    invoking_repo = Repo(os.getcwd())
    branch_name = invoking_repo.active_branch.name

    if branch_name == "main":
        logger.error("Cannot run mr-update on the main branch.")
        sys.exit(1)

    if not is_ai_cli_installed():
        logger.error("AI CLI not installed.")
        sys.exit(1)

    mr = _get_mr_for_current_branch(invoking_repo)
    target_branch = mr.target_branch
    # Run from the branch's own checkout, which for this command is normally the
    # invoking one, so the merge lands where it is expected.
    worktree = acquire_mr_worktree(mr, invoking_repo)
    repo = worktree.repo
    print(f"Worktree: {worktree.path}")

    print("Fetching origin...")
    repo.remotes.origin.fetch()

    ahead_commits = list(repo.iter_commits(f"HEAD..origin/{target_branch}"))
    if not ahead_commits:
        print(f"Branch is already up to date with origin/{target_branch}.")
        return

    print(f"origin/{target_branch} has {len(ahead_commits)} new commit(s) — merging...")

    head_before = repo.head.commit.hexsha
    conflicting: list[str] = []
    try:
        repo.git.merge(f"origin/{target_branch}", "--no-edit")
        print(f"Merged origin/{target_branch} cleanly.")
    except GitCommandError as e:
        logger.warning(
            "git merge failed (status %s):\nstdout: %s\nstderr: %s",
            e.status,
            e.stdout,
            e.stderr,
        )
        conflicting = repo.git.diff("--name-only", "--diff-filter=U").splitlines()
        if not conflicting and repo.head.commit.hexsha == head_before:
            try:
                repo.git.merge("--abort")
            except GitCommandError:
                pass
            logger.error("Merge failed with no changes — aborting.")
            sys.exit(1)
        if conflicting:
            print(
                f"Merge conflict in {len(conflicting)} file(s): {', '.join(conflicting)}"
            )

    if conflicting:
        _resolve_conflicts_and_commit(worktree, conflicting, target_branch)

    repo.git.push("origin", branch_name)
    print(f"Pushed {branch_name} to origin.")
