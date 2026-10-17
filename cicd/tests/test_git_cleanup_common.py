"""Unit tests for the helpers shared by the branch and worktree cleanup scripts.

The git-backed helpers are exercised against real repositories rather than faked command
output, because what they read — which branch a worktree holds, which branches are
therefore undeletable — is exactly what a test double would get wrong.
"""

from pathlib import Path
from typing import List

import pytest
from git import Repo

from git_cleanup_common import (
    Answer,
    checked_out_branches,
    confirm_each,
    human_bytes,
    list_worktrees,
    main_worktree_path,
    parse_answer,
    parse_worktree_list,
    run_git,
)

PORCELAIN = """worktree /repo
HEAD 1111111111111111111111111111111111111111
branch refs/heads/main

worktree /repo-worktrees/feature
HEAD 2222222222222222222222222222222222222222
branch refs/heads/feature/thing

worktree /repo-worktrees/detached
HEAD 3333333333333333333333333333333333333333
detached
"""


def _configure(repo: Repo) -> None:
    """Pin settings so the temp repos do not inherit the developer's git config."""
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test")
    repo.git.config("commit.gpgsign", "false")
    repo.git.config("core.hooksPath", "/dev/null")


@pytest.fixture(name="repo_path")
def fixture_repo_path(tmp_path: Path) -> Path:
    """A repository with one commit on main."""
    path = tmp_path / "repo"
    path.mkdir()
    repo = Repo.init(path, initial_branch="main")
    _configure(repo)
    (path / "file.txt").write_text("hello", encoding="utf-8")
    repo.index.add(["file.txt"])
    repo.index.commit("initial")
    return path


class TestParseWorktreeList:
    """The porcelain parser is a pure function over git's documented format."""

    def test_reads_every_record(self) -> None:
        refs = parse_worktree_list(PORCELAIN)
        assert [ref.path for ref in refs] == [
            Path("/repo"),
            Path("/repo-worktrees/feature"),
            Path("/repo-worktrees/detached"),
        ]

    def test_strips_the_refs_heads_prefix(self) -> None:
        refs = parse_worktree_list(PORCELAIN)
        assert refs[1].branch == "feature/thing"

    def test_detached_worktree_has_no_branch(self) -> None:
        """A detached record must not inherit the previous record's branch."""
        refs = parse_worktree_list(PORCELAIN)
        assert refs[2].branch is None

    def test_empty_input(self) -> None:
        assert not parse_worktree_list("")


class TestAgainstARealRepository:
    """Worktree discovery, run against git itself."""

    def test_lists_the_primary_checkout(self, repo_path: Path) -> None:
        refs = list_worktrees(repo_path)
        assert [ref.path.resolve() for ref in refs] == [repo_path.resolve()]

    def test_finds_an_added_worktree(self, repo_path: Path) -> None:
        linked = repo_path.parent / "linked"
        run_git(["worktree", "add", "-b", "side", str(linked)], repo_path)

        branches = checked_out_branches(repo_path)
        assert branches == {"main", "side"}

    def test_main_worktree_path_is_the_primary_checkout(self, repo_path: Path) -> None:
        """Resolved from a linked worktree, it must still point at the original."""
        linked = repo_path.parent / "linked"
        run_git(["worktree", "add", "-b", "side", str(linked)], repo_path)

        assert main_worktree_path(linked).resolve() == repo_path.resolve()


class TestHumanBytes:
    """Byte formatting."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0, "0B"),
            (512, "512B"),
            (1024, "1.0K"),
            (1024 * 1024, "1.0M"),
            (3 * 1024**3, "3.0G"),
            (None, "?"),
        ],
    )
    def test_formats(self, value: int, expected: str) -> None:
        assert human_bytes(value) == expected


class TestParseAnswer:
    """Reply parsing, including the default."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("y", Answer.YES),
            ("YES", Answer.YES),
            ("n", Answer.NO),
            ("", Answer.NO),
            ("  A  ", Answer.ALL),
            ("quit", Answer.QUIT),
        ],
    )
    def test_understood(self, raw: str, expected: Answer) -> None:
        assert parse_answer(raw) == expected

    def test_bare_enter_declines(self) -> None:
        """An empty reply must never be read as consent to delete."""
        assert parse_answer("") is Answer.NO

    def test_unrecognised(self) -> None:
        assert parse_answer("maybe") is None


class TestConfirmEach:
    """The walk reports one decision per item, whatever the operator types."""

    @staticmethod
    def _run(items: List[str], replies: List[Answer]) -> List[bool]:
        remaining = list(replies)

        def asker(_question: str, assume_yes: bool) -> Answer:
            if assume_yes:
                return Answer.YES
            return remaining.pop(0)

        return [
            decision.accepted
            for decision in confirm_each(items, lambda _item: None, "?", asker)
        ]

    def test_individual_replies(self) -> None:
        assert self._run(["a", "b", "c"], [Answer.YES, Answer.NO, Answer.YES]) == [
            True,
            False,
            True,
        ]

    def test_all_accepts_the_remainder(self) -> None:
        assert self._run(["a", "b", "c"], [Answer.NO, Answer.ALL]) == [
            False,
            True,
            True,
        ]

    def test_quit_rejects_the_remainder(self) -> None:
        """Quitting must not silently accept what was never shown."""
        assert self._run(["a", "b", "c"], [Answer.YES, Answer.QUIT]) == [
            True,
            False,
            False,
        ]

    def test_every_item_is_reported(self) -> None:
        """The caller tallies from the decisions, so none may be dropped."""
        items = ["a", "b", "c", "d"]
        assert len(self._run(items, [Answer.QUIT])) == len(items)
