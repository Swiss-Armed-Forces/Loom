"""Shared git helpers for the branch and worktree cleanup scripts.

`git_delete_merged_branches.py` and `git_cleanup_worktrees.py` both need to run git,
enumerate worktrees and ask the operator a yes/no question, so those live here rather
than in either of them.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Callable,
    Generic,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
)

ItemT = TypeVar("ItemT")


class CommandResult(NamedTuple):
    """Outcome of a subprocess call."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Whether the command exited successfully."""
        return self.returncode == 0

    @property
    def out(self) -> str:
        """Standard output with surrounding whitespace removed."""
        return self.stdout.strip()


def run_command(args: Sequence[str], cwd: Optional[Path] = None) -> CommandResult:
    """Run a command, capturing its output and never raising on failure."""
    completed = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def run_git(args: Sequence[str], cwd: Path) -> CommandResult:
    """Run a git subcommand in the given directory."""
    return run_command(["git", *args], cwd=cwd)


@dataclass(frozen=True)
class WorktreeRef:
    """A worktree as `git worktree list --porcelain` reports it."""

    path: Path
    branch: Optional[str]

    @property
    def name(self) -> str:
        """Short label for display."""
        return self.path.name


def parse_worktree_list(porcelain: str) -> List[WorktreeRef]:
    """Parse the output of `git worktree list --porcelain`.

    A record starts at its `worktree` line and runs until the next one; a detached
    worktree has no `branch` line at all.
    """
    worktrees: List[WorktreeRef] = []
    path: Optional[Path] = None
    branch: Optional[str] = None

    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            if path is not None:
                worktrees.append(WorktreeRef(path, branch))
            path = Path(line[len("worktree ") :])
            branch = None
        elif line.startswith("branch "):
            branch = line[len("branch ") :].removeprefix("refs/heads/")
    if path is not None:
        worktrees.append(WorktreeRef(path, branch))
    return worktrees


def list_worktrees(repo: Path) -> List[WorktreeRef]:
    """Return every worktree of the repository, primary checkout included."""
    result = run_git(["worktree", "list", "--porcelain"], cwd=repo)
    if not result.ok:
        return []
    return parse_worktree_list(result.stdout)


def main_worktree_path(repo: Path) -> Path:
    """Return the repository's primary checkout."""
    result = run_git(["rev-parse", "--git-common-dir"], cwd=repo)
    common = Path(result.out)
    if not common.is_absolute():
        common = (repo / common).resolve()
    return common.parent


def checked_out_branches(repo: Path) -> set[str]:
    """Return the branches that some worktree currently has checked out.

    git refuses to delete these, so a cleanup script has to skip them rather than fail
    on them.
    """
    return {
        worktree.branch
        for worktree in list_worktrees(repo)
        if worktree.branch is not None
    }


def human_bytes(num_bytes: Optional[int]) -> str:
    """Format a byte count the way `du -h` would."""
    if num_bytes is None:
        return "?"
    size = float(num_bytes)
    for unit in ("B", "K", "M", "G", "T"):
        if abs(size) < 1024.0:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}P"


def directory_size(path: Path) -> Optional[int]:
    """Return a directory's size in bytes, or None when it cannot be measured."""
    result = run_command(["du", "-sb", str(path)])
    if not result.ok:
        return None
    try:
        return int(result.out.split()[0])
    except (ValueError, IndexError):
        return None


class Answer(Enum):
    """Reply to a yes/no/all/quit prompt."""

    YES = "yes"
    NO = "no"
    ALL = "all"
    QUIT = "quit"


_ANSWERS = {
    "y": Answer.YES,
    "yes": Answer.YES,
    "n": Answer.NO,
    "no": Answer.NO,
    "": Answer.NO,
    "a": Answer.ALL,
    "all": Answer.ALL,
    "q": Answer.QUIT,
    "quit": Answer.QUIT,
}


def parse_answer(raw: str) -> Optional[Answer]:
    """Map a typed reply onto an Answer, or None when it is not understood."""
    return _ANSWERS.get(raw.strip().lower())


def prompt(question: str, assume_yes: bool = False) -> Answer:
    """Ask a yes/no/all/quit question.

    Defaults to no, so a bare Enter and a non-interactive stdin both decline.
    """
    if assume_yes:
        return Answer.YES
    if not sys.stdin.isatty():
        return Answer.NO
    while True:
        answer = parse_answer(input(f"{question} [y/N/a/q] "))
        if answer is not None:
            return answer
        print("  please answer y, n, a (all remaining) or q (quit)")


@dataclass(frozen=True)
class Decision(Generic[ItemT]):
    """One item and whether the operator accepted it."""

    item: ItemT
    accepted: bool


def confirm_each(
    items: Sequence[ItemT],
    describe: Callable[[ItemT], None],
    question: str,
    asker: Callable[[str, bool], Answer] = prompt,
) -> Iterator[Decision[ItemT]]:
    """Ask about each item in turn, yielding a Decision for every one.

    "all" accepts the rest without further prompting and "quit" rejects the rest, so the
    caller always sees one Decision per item and can tally them without tracking where
    the walk stopped.

    `asker` exists so tests can supply replies without driving stdin.
    """
    assume_yes = False
    quitting = False
    for item in items:
        if quitting:
            yield Decision(item, False)
            continue

        describe(item)
        answer = asker(question, assume_yes)
        if answer is Answer.QUIT:
            quitting = True
            yield Decision(item, False)
            continue
        if answer is Answer.ALL:
            assume_yes = True
            answer = Answer.YES
        yield Decision(item, answer is Answer.YES)


def add_repo_argument(parser: argparse.ArgumentParser) -> None:
    """Add the --repo option shared by the cleanup scripts."""
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="repository to operate on (default: current directory)",
    )
