#!/usr/bin/env python3
"""Interactively remove git worktrees whose merge request is finished.

Worktrees are classified from three facts: the state of the merge request whose source
branch the worktree holds, whether the working tree is clean, and whether every commit
is on the branch's remote. A worktree that is merged, clean and pushed carries nothing
that `git worktree add` cannot recreate, so it goes without asking. Everything else is
confirmed one at a time.

Ancestry cannot answer this on its own: Loom squash-merges, so a merged branch is never
an ancestor of main. The merge request state is the authority, read through `glab`.

Removing a worktree never deletes its branch.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence

from git_cleanup_common import (
    Answer,
    WorktreeRef,
    add_repo_argument,
    confirm_each,
    directory_size,
    human_bytes,
    list_worktrees,
    main_worktree_path,
    prompt,
    run_command,
    run_git,
)

# Regenerable directories, relative to a worktree root. pytest.ini redirects
# test scratch out of /tmp into these; nothing here outlives a test run.
PURGE_TARGETS = (
    "backend/.pytest_tmp",
    "backend/.pytest_cache",
    ".pytest_cache",
)


class MergeRequestState(str, Enum):
    """State of the merge request whose source branch a worktree holds."""

    MERGED = "merged"
    CLOSED = "closed"
    OPENED = "opened"
    NONE = "no merge request"
    UNKNOWN = "unknown"


class Verdict(str, Enum):
    """What the script intends to do with a worktree."""

    REMOVE = "remove"
    ASK = "ask"
    KEEP = "keep"


class MergeRequestLookup(NamedTuple):
    """What `glab` said about a branch's merge requests."""

    state: MergeRequestState
    label: str


class MergeRequestSummary(NamedTuple):
    """One merge request, reduced to the two fields that matter here."""

    iid: int
    state: str


class MergeRequestFetch(NamedTuple):
    """Raw result of asking glab about a branch.

    `error` is set when the question could not be answered at all, which is different
    from the branch genuinely having no merge request.
    """

    summaries: List[MergeRequestSummary]
    error: Optional[str]


@dataclass
class WorktreeInfo:
    """Everything the classification needs about a single worktree."""

    ref: WorktreeRef
    dirty_files: int
    unpushed: int
    lookup: MergeRequestLookup
    size_bytes: Optional[int] = None
    verdict: Verdict = Verdict.ASK
    reasons: List[str] = field(default_factory=list)

    @property
    def path(self) -> Path:
        """Where the worktree lives."""
        return self.ref.path

    @property
    def name(self) -> str:
        """Short label for display."""
        return self.ref.name

    @property
    def branch(self) -> Optional[str]:
        """The branch the worktree has checked out."""
        return self.ref.branch

    @property
    def needs_force(self) -> bool:
        """Whether git will refuse to remove this worktree without --force."""
        return self.dirty_files > 0


@dataclass
class Totals:
    """Running tally of what the session removed."""

    removed: int = 0
    freed_bytes: int = 0
    purged_bytes: int = 0
    kept: int = 0


@dataclass(frozen=True)
class Options:
    """The parsed command line."""

    dry_run: bool
    yes: bool
    purge_scratch: bool
    no_fetch: bool
    no_mr: bool
    no_size: bool
    repo: Path


def fetch_merge_requests(branch: str) -> MergeRequestFetch:
    """Ask glab for every merge request opened from this branch."""
    if shutil.which("glab") is None:
        return MergeRequestFetch([], "glab not installed")

    query = urllib.parse.quote(branch, safe="")
    result = run_command(
        [
            "glab",
            "api",
            f"projects/:id/merge_requests?source_branch={query}&state=all&per_page=20",
        ]
    )
    if not result.ok:
        return MergeRequestFetch([], "glab query failed")

    try:
        payload = json.loads(result.stdout)
        summaries = [
            MergeRequestSummary(int(entry["iid"]), str(entry["state"]))
            for entry in payload
        ]
    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
        return MergeRequestFetch([], "unreadable glab response")

    return MergeRequestFetch(summaries, None)


def interpret_merge_requests(fetched: MergeRequestFetch) -> MergeRequestLookup:
    """Decide what a branch's merge requests say about it.

    A branch with several merge requests counts as finished only when none of them is
    still open, so one reopened merge request keeps the whole worktree.
    """
    if fetched.error is not None:
        return MergeRequestLookup(MergeRequestState.UNKNOWN, fetched.error)
    if not fetched.summaries:
        return MergeRequestLookup(MergeRequestState.NONE, "no merge request")

    label = " ".join(f"!{mr.iid}:{mr.state}" for mr in fetched.summaries)
    states = {mr.state for mr in fetched.summaries}
    if "opened" in states:
        return MergeRequestLookup(MergeRequestState.OPENED, label)
    if "merged" in states:
        return MergeRequestLookup(MergeRequestState.MERGED, label)
    return MergeRequestLookup(MergeRequestState.CLOSED, label)


def merge_request_state(branch: str) -> MergeRequestLookup:
    """Ask GitLab about a branch and interpret the answer."""
    return interpret_merge_requests(fetch_merge_requests(branch))


def count_dirty(path: Path) -> int:
    """Count uncommitted changes, untracked files included."""
    if not path.exists():
        return 0
    result = run_git(["status", "--porcelain"], path)
    if not result.ok:
        return 0
    return len([line for line in result.stdout.splitlines() if line.strip()])


def count_unpushed(repo: Path, branch: str) -> int:
    """Count commits on the branch that its own remote branch lacks."""
    result = run_git(["rev-list", "--count", f"origin/{branch}..{branch}"], repo)
    if not result.ok:
        return 0
    try:
        return int(result.out)
    except ValueError:
        return 0


def has_remote_branch(repo: Path, branch: str) -> bool:
    """Whether origin still carries this branch."""
    ref = f"refs/remotes/origin/{branch}"
    return run_git(["show-ref", "--verify", "--quiet", ref], repo).ok


def describe(
    repo: Path, ref: WorktreeRef, options: Options, here: Path
) -> WorktreeInfo:
    """Gather state for one worktree and decide what should happen to it."""
    unpushed = 0
    if ref.branch is not None and has_remote_branch(repo, ref.branch):
        unpushed = count_unpushed(repo, ref.branch)

    if options.no_mr or ref.branch is None:
        lookup = MergeRequestLookup(MergeRequestState.UNKNOWN, "not checked")
    else:
        lookup = merge_request_state(ref.branch)

    info = WorktreeInfo(
        ref=ref,
        dirty_files=count_dirty(ref.path),
        unpushed=unpushed,
        lookup=lookup,
        size_bytes=None if options.no_size else directory_size(ref.path),
    )
    classify(info, here)
    return info


def is_inside(here: Path, path: Path) -> bool:
    """Whether the current directory sits in this worktree."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return here == resolved or here.is_relative_to(resolved)


def classify(info: WorktreeInfo, here: Path) -> None:
    """Set the verdict and the reasons shown to the operator."""
    if is_inside(here, info.path):
        info.verdict = Verdict.KEEP
        info.reasons.append("you are standing in it")
        return

    if not info.path.exists():
        info.verdict = Verdict.ASK
        info.reasons.append("directory is gone (prunable)")
        return

    state = info.lookup.state
    label = info.lookup.label

    if state is MergeRequestState.OPENED:
        info.verdict = Verdict.KEEP
        info.reasons.append(f"merge request still open ({label})")
        return

    blockers: List[str] = []
    if info.dirty_files:
        blockers.append(f"{info.dirty_files} uncommitted change(s)")
    if info.unpushed:
        blockers.append(f"{info.unpushed} unpushed commit(s)")

    if state is MergeRequestState.MERGED and not blockers:
        info.verdict = Verdict.REMOVE
        info.reasons.append(f"merged ({label}), clean, fully pushed")
        return

    info.verdict = Verdict.ASK
    if state is MergeRequestState.MERGED:
        info.reasons.append(f"merged ({label}) but " + ", ".join(blockers))
    elif state is MergeRequestState.CLOSED:
        info.reasons.append(f"merge request closed without merging ({label})")
        info.reasons.extend(blockers)
    elif state is MergeRequestState.NONE:
        info.reasons.append("no merge request was ever opened")
        info.reasons.extend(blockers)
    else:
        info.reasons.append(f"merge request state unknown ({label})")
        info.reasons.extend(blockers)


def collect(options: Options) -> List[WorktreeInfo]:
    """Build a WorktreeInfo for every worktree except the primary checkout."""
    repo = options.repo
    primary = main_worktree_path(repo).resolve()
    here = Path.cwd().resolve()

    return [
        describe(repo, ref, options, here)
        for ref in list_worktrees(repo)
        if ref.path.resolve() != primary
    ]


def remove(repo: Path, info: WorktreeInfo, dry_run: bool) -> bool:
    """Remove one worktree, forcing only when it carries uncommitted work."""
    args = ["worktree", "remove"]
    if info.needs_force:
        args.append("--force")
    args.append(str(info.path))

    if dry_run:
        print(f"    would run: git {' '.join(args)}")
        return True

    result = run_git(args, repo)
    if not result.ok:
        print(f"    FAILED: {result.stderr.strip()}")
        return False
    print(f"    removed ({human_bytes(info.size_bytes)} freed)")
    return True


def purge_scratch(roots: Sequence[Path], dry_run: bool) -> int:
    """Delete regenerable test scratch from the given worktree roots."""
    freed = 0
    for root in roots:
        for target in PURGE_TARGETS:
            victim = root / target
            if not victim.is_dir():
                continue
            size = directory_size(victim) or 0
            freed += size
            verb = "would purge" if dry_run else "purging   "
            print(f"  {verb} {human_bytes(size):>8}  {victim}")
            if not dry_run:
                shutil.rmtree(victim, ignore_errors=True)
    return freed


def report_orphans(container: Path, worktrees: Sequence[WorktreeInfo]) -> None:
    """List directories beside the worktrees that git does not know about."""
    if not container.is_dir():
        return
    known = {info.path.resolve() for info in worktrees}
    orphans = [
        child
        for child in sorted(container.iterdir())
        if child.is_dir() and child.resolve() not in known
    ]
    if not orphans:
        return
    print(f"\nDirectories in {container} that are not worktrees (never touched):")
    for orphan in orphans:
        print(f"  {human_bytes(directory_size(orphan)):>8}  {orphan.name}")
    print("  Review and delete these by hand if you want them gone.")


def show(info: WorktreeInfo) -> None:
    """Print one worktree's heading and the reasons behind its verdict."""
    print(f"\n  {info.name}  ({human_bytes(info.size_bytes)})")
    print(f"    branch: {info.branch or '(detached)'}")
    for reason in info.reasons:
        print(f"    - {reason}")


def show_with_warning(info: WorktreeInfo) -> None:
    """Print a worktree ahead of its prompt, flagging work that would be lost."""
    show(info)
    if info.needs_force:
        print("    NOTE: removing this DISCARDS the uncommitted changes")


def handle_finished(
    options: Options, finished: Sequence[WorktreeInfo], totals: Totals
) -> bool:
    """Offer the merged worktrees as one block.

    Returns False to stop the run.
    """
    if not finished:
        return True

    reclaim = sum(info.size_bytes or 0 for info in finished)
    print(f"\n=== Finished: {len(finished)}, {human_bytes(reclaim)} ===")
    for info in finished:
        show(info)

    skip_question = options.yes or options.dry_run
    answer = Answer.YES if skip_question else prompt("\nRemove all of these?")
    if answer is Answer.QUIT:
        return False
    if answer is Answer.NO:
        totals.kept += len(finished)
        return True

    for info in finished:
        print(f"\n  {info.name}")
        if remove(options.repo, info, options.dry_run):
            totals.removed += 1
            totals.freed_bytes += info.size_bytes or 0
    return True


def handle_uncertain(
    options: Options, uncertain: Sequence[WorktreeInfo], totals: Totals
) -> None:
    """Walk the worktrees that need a decision, one prompt each."""
    if not uncertain:
        return

    print(f"\n=== Needs a decision: {len(uncertain)} ===")
    if options.yes and not options.dry_run:
        print("  --yes given, so these are left alone. Rerun interactively.")
        totals.kept += len(uncertain)
        return

    for decision in confirm_each(uncertain, show_with_warning, "    Remove it?"):
        if not decision.accepted:
            totals.kept += 1
        elif remove(options.repo, decision.item, options.dry_run):
            totals.removed += 1
            totals.freed_bytes += decision.item.size_bytes or 0


def parse_args(argv: Optional[Sequence[str]] = None) -> Options:
    """Build the command line."""
    parser = argparse.ArgumentParser(
        prog="git-cleanup-worktrees",
        description=(
            "Remove git worktrees whose merge request is finished. Merged, "
            "clean, fully pushed worktrees go without asking; anything else is "
            "confirmed one at a time. Branches are never deleted."
        ),
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="show the plan, change nothing"
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="remove the merged ones without the confirmation prompt; uncertain "
        "worktrees are still kept, never removed",
    )
    parser.add_argument(
        "--purge-scratch",
        action="store_true",
        help="also delete regenerable test scratch "
        f"({', '.join(PURGE_TARGETS)}) from the worktrees that survive",
    )
    parser.add_argument(
        "--no-fetch", action="store_true", help="skip git fetch before deciding"
    )
    parser.add_argument(
        "--no-mr",
        action="store_true",
        help="do not query GitLab; every worktree becomes a question",
    )
    parser.add_argument(
        "--no-size", action="store_true", help="skip size measurement (much faster)"
    )
    add_repo_argument(parser)
    args = parser.parse_args(argv)
    return Options(
        dry_run=args.dry_run,
        yes=args.yes,
        purge_scratch=args.purge_scratch,
        no_fetch=args.no_fetch,
        no_mr=args.no_mr,
        no_size=args.no_size,
        repo=args.repo.resolve(),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point."""
    options = parse_args(argv)

    if not run_git(["rev-parse", "--git-dir"], options.repo).ok:
        print(f"error: not a git repository: {options.repo}", file=sys.stderr)
        return 1

    if not options.no_fetch and not options.dry_run:
        print("Fetching origin ...")
        run_git(["fetch", "--prune", "origin"], options.repo)

    print("Inspecting worktrees ...")
    worktrees = collect(options)
    if not worktrees:
        print("No worktrees besides the primary checkout.")
        return 0

    finished = [info for info in worktrees if info.verdict is Verdict.REMOVE]
    uncertain = [info for info in worktrees if info.verdict is Verdict.ASK]
    keep = [info for info in worktrees if info.verdict is Verdict.KEEP]
    totals = Totals()

    if keep:
        print(f"\n=== Keeping {len(keep)} ===")
        for info in keep:
            show(info)
        totals.kept += len(keep)

    if handle_finished(options, finished, totals):
        handle_uncertain(options, uncertain, totals)

    if options.purge_scratch:
        print("\n=== Purging regenerable test scratch ===")
        survivors = [options.repo] + [
            info.path for info in worktrees if info.path.exists()
        ]
        totals.purged_bytes = purge_scratch(survivors, options.dry_run)

    if not options.dry_run:
        run_git(["worktree", "prune"], options.repo)

    report_orphans(
        worktrees[0].path.parent, [info for info in worktrees if info.path.exists()]
    )

    verb = "Would free" if options.dry_run else "Freed"
    total = totals.freed_bytes + totals.purged_bytes
    print(
        f"\n{verb} {human_bytes(total)} "
        f"({totals.removed} worktree(s) removed, {totals.kept} kept)."
    )
    if totals.purged_bytes:
        print(f"  of which {human_bytes(totals.purged_bytes)} was test scratch.")
    print("Branches were not deleted; re-add any worktree with `git worktree add`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
