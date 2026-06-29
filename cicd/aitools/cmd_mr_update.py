import argparse
import logging
import os
import sys
import tempfile

from git import Repo
from git.exc import GitCommandError

from .claude import is_claude_cli_installed, run_claude_agentic
from .prompts import build_merge_conflict_prompt

logger = logging.getLogger(__name__)


def cmd_mr_update(_args: argparse.Namespace) -> None:
    """Merge origin/main into the current branch, resolve any conflicts, and push."""
    repo = Repo(os.getcwd())
    branch_name = repo.active_branch.name

    if branch_name == "main":
        logger.error("Cannot run mr-update on the main branch.")
        sys.exit(1)

    if not is_claude_cli_installed():
        logger.error("Claude CLI not installed.")
        sys.exit(1)

    print("Fetching origin...")
    repo.remotes.origin.fetch()

    ahead_commits = list(repo.iter_commits("HEAD..origin/main"))
    if not ahead_commits:
        print("Branch is already up to date with origin/main.")
        return

    print(f"origin/main has {len(ahead_commits)} new commit(s) — merging...")

    head_before = repo.head.commit.hexsha
    conflicting: list[str] = []
    try:
        repo.git.merge("origin/main", "--no-edit")
        print("Merged origin/main cleanly.")
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
        with tempfile.TemporaryDirectory(
            prefix=".loom_mrupdate_", dir=repo.working_dir
        ) as ctx:
            with open(os.path.join(ctx, "conflicts.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(conflicting))
            run_claude_agentic(
                build_merge_conflict_prompt(branch_name, conflicting, ctx), repo
            )
        repo.git.add("-A")
        repo.git.commit(
            "--no-verify", "-m", f"chore: merge origin/main into {branch_name}"
        )
        print("Resolved merge conflicts and committed.")

    repo.git.push("origin", branch_name)
    print(f"Pushed {branch_name} to origin.")
