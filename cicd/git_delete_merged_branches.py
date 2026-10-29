#!/usr/bin/env python3
"""Delete local git branches that have been merged into the main branch.

Two kinds of merge are recognised. A *regular* merge leaves the branch as an ancestor of
main, which `git branch --merged` reports. A *squash* merge does not: main carries one
new commit whose tree contains the branch's changes but whose history does not contain
the branch. This project squash-merges, so that second case is the one that matters, and
it is detected by replaying the branch's tree onto the merge base and asking `git
cherry` whether main already has an equivalent commit.

Branches checked out in any worktree are skipped — git refuses to delete those, and
failing on them would abort the run.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence

from git_cleanup_common import (
    CommandResult,
    add_repo_argument,
    checked_out_branches,
    confirm_each,
    run_git,
)


class DeleteMode(str, Enum):
    """Which kinds of merged branch to consider."""

    ALL = "all"
    SQUASH = "squash"
    MERGED = "merged"


class MergeKind(str, Enum):
    """How a branch reached the main branch."""

    SQUASH = "squash-merged"
    REGULAR = "merged"


@dataclass(frozen=True)
class Candidate:
    """A branch that may be deleted, and why."""

    name: str
    kind: MergeKind

    @property
    def force(self) -> bool:
        """Whether git needs -D rather than -d to delete it.

        A squash-merged branch is not an ancestor of main, so the safe delete refuses
        it.
        """
        return self.kind is MergeKind.SQUASH


@dataclass
class Report:
    """Tally of one run."""

    deleted: int = 0
    skipped: int = 0
    failed: int = 0


def local_branches(repo: Path) -> List[str]:
    """Return every local branch name."""
    result = run_git(["for-each-ref", "refs/heads/", "--format=%(refname:short)"], repo)
    if not result.ok:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_squash_merged(repo: Path, branch: str, main_branch: str) -> bool:
    """Report whether main already contains this branch's changes.

    Builds a throwaway commit holding the branch's tree on top of the merge base, then
    asks `git cherry` whether main carries an equivalent patch. The temporary commit is
    never referenced and is collected by `git gc`.
    """
    merge_base: CommandResult = run_git(["merge-base", main_branch, branch], repo)
    if not merge_base.ok or not merge_base.out:
        return False

    tree = run_git(["rev-parse", f"{branch}^{{tree}}"], repo)
    if not tree.ok or not tree.out:
        return False

    replayed = run_git(
        ["commit-tree", tree.out, "-p", merge_base.out, "-m", "_"],
        repo,
    )
    if not replayed.ok or not replayed.out:
        return False

    cherry = run_git(["cherry", main_branch, replayed.out], repo)
    if not cherry.ok:
        return False

    # "-" means an equivalent patch is already upstream; "+" means it is not.
    return cherry.out.startswith("-")


def regularly_merged(repo: Path, main_branch: str) -> List[str]:
    """Return branches that are ancestors of the main branch."""
    result = run_git(
        ["branch", "--merged", main_branch, "--format=%(refname:short)"], repo
    )
    if not result.ok:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_candidates(repo: Path, main_branch: str, mode: DeleteMode) -> List[Candidate]:
    """Collect every branch eligible for deletion under this mode."""
    protected = checked_out_branches(repo) | {main_branch}
    candidates: List[Candidate] = []
    seen: set[str] = set()

    if mode in (DeleteMode.ALL, DeleteMode.MERGED):
        for branch in regularly_merged(repo, main_branch):
            if branch in protected or branch in seen:
                continue
            seen.add(branch)
            candidates.append(Candidate(branch, MergeKind.REGULAR))

    if mode in (DeleteMode.ALL, DeleteMode.SQUASH):
        for branch in local_branches(repo):
            if branch in protected or branch in seen:
                continue
            if is_squash_merged(repo, branch, main_branch):
                seen.add(branch)
                candidates.append(Candidate(branch, MergeKind.SQUASH))

    return sorted(candidates, key=lambda candidate: candidate.name)


def delete_branch(repo: Path, candidate: Candidate, dry_run: bool) -> bool:
    """Delete one branch.

    Returns whether it is now gone.
    """
    flag = "-D" if candidate.force else "-d"
    if dry_run:
        print(f"  [dry run] would delete {candidate.kind.value}: {candidate.name}")
        return True

    result = run_git(["branch", flag, candidate.name], repo)
    if not result.ok:
        print(f"  FAILED {candidate.name}: {result.stderr.strip()}")
        return False
    print(f"  deleted {candidate.kind.value}: {candidate.name}")
    return True


def report_protected(repo: Path, main_branch: str) -> None:
    """Explain which branches were never considered."""
    held = sorted(checked_out_branches(repo) - {main_branch})
    if held:
        print("\nChecked out in a worktree, so left alone:")
        for branch in held:
            print(f"  {branch}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Build the command line."""
    parser = argparse.ArgumentParser(
        prog="git-delete-merged-branches",
        description="Delete local git branches that have been merged into the "
        "main branch, including squash-merged ones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "delete types:\n"
            "  all     both squash-merged and regularly merged branches\n"
            "  squash  only squash-merged branches\n"
            "  merged  only regularly merged branches\n\n"
            "examples:\n"
            "  git-delete-merged-branches -n          dry run\n"
            "  git-delete-merged-branches -m develop  use develop as main\n"
            "  git-delete-merged-branches -t squash   only squash-merged\n"
            "  git-delete-merged-branches -i          confirm each branch\n"
        ),
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="dry run mode (do not actually delete branches)",
    )
    parser.add_argument(
        "-m",
        "--main-branch",
        default=os.environ.get("MAIN_BRANCH", "main"),
        help="specify main branch (default: main, or $MAIN_BRANCH)",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="mode",
        type=DeleteMode,
        choices=list(DeleteMode),
        default=DeleteMode.ALL,
        help="delete type: all, squash, merged (default: all)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="confirm each branch before deleting it",
    )
    add_repo_argument(parser)
    return parser.parse_args(argv)


def show_candidate(candidate: Candidate) -> None:
    """Print one candidate ahead of its prompt."""
    print(f"\n  {candidate.name}  ({candidate.kind.value})")


def delete_confirmed(
    repo: Path, candidates: Sequence[Candidate], dry_run: bool
) -> Report:
    """Walk the candidates one at a time, asking before each deletion."""
    report = Report()
    for decision in confirm_each(candidates, show_candidate, "    Delete it?"):
        if not decision.accepted:
            report.skipped += 1
        elif delete_branch(repo, decision.item, dry_run):
            report.deleted += 1
        else:
            report.failed += 1
    return report


def delete_all(repo: Path, candidates: Sequence[Candidate], dry_run: bool) -> Report:
    """Delete every candidate without asking."""
    report = Report()
    for candidate in candidates:
        if delete_branch(repo, candidate, dry_run):
            report.deleted += 1
        else:
            report.failed += 1
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    repo: Path = args.repo.resolve()

    if not run_git(["rev-parse", "--git-dir"], repo).ok:
        print(f"error: not a git repository: {repo}", file=sys.stderr)
        return 1

    if not run_git(["rev-parse", "--verify", args.main_branch], repo).ok:
        print(f"error: no such branch: {args.main_branch}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("DRY RUN MODE - No branches will be deleted")

    print(f"Looking for branches merged into {args.main_branch} ...")
    candidates = find_candidates(repo, args.main_branch, args.mode)

    if not candidates:
        print("No merged branches to delete.")
        report_protected(repo, args.main_branch)
        return 0

    print(f"\nFound {len(candidates)} branch(es) already in {args.main_branch}:")
    for candidate in candidates:
        print(f"  {candidate.name}  ({candidate.kind.value})")

    if args.interactive:
        report = delete_confirmed(repo, candidates, args.dry_run)
    else:
        print()
        report = delete_all(repo, candidates, args.dry_run)

    report_protected(repo, args.main_branch)

    verb = "would delete" if args.dry_run else "deleted"
    print(f"\n{verb} {report.deleted}, kept {report.skipped}, failed {report.failed}.")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
