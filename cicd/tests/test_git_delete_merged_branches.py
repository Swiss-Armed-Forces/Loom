"""Unit tests for squash-merge detection.

Loom squash-merges, so `git branch --merged` reports almost nothing and the interesting
path is the one that replays a branch's tree onto the merge base. These tests build real
repositories and really squash-merge into them, because the detection is a statement
about git's own object graph.
"""

from pathlib import Path

import pytest
from git import Repo

from git_cleanup_common import run_git
from git_delete_merged_branches import (
    Candidate,
    DeleteMode,
    MergeKind,
    find_candidates,
    is_squash_merged,
)


def _configure(repo: Repo) -> None:
    """Pin settings so the temp repos do not inherit the developer's git config."""
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test")
    repo.git.config("commit.gpgsign", "false")
    repo.git.config("core.hooksPath", "/dev/null")


def _commit(repo: Repo, name: str, content: str) -> None:
    path = Path(str(repo.working_dir)) / name
    path.write_text(content, encoding="utf-8")
    repo.index.add([name])
    repo.index.commit(f"add {name}")


@pytest.fixture(name="repo")
def fixture_repo(tmp_path: Path) -> Repo:
    """A repository with a single commit on main."""
    path = tmp_path / "repo"
    path.mkdir()
    repo = Repo.init(path, initial_branch="main")
    _configure(repo)
    _commit(repo, "base.txt", "base")
    return repo


def _branch_with_work(repo: Repo, name: str, content: str = "work") -> None:
    """Create a branch, commit on it and return to main."""
    repo.git.checkout("-b", name)
    _commit(repo, f"{name}.txt", content)
    repo.git.checkout("main")


def _squash_merge(repo: Repo, name: str) -> None:
    """Land a branch the way GitLab's squash merge does: one new commit on main."""
    repo.git.merge("--squash", name)
    repo.index.commit(f"squash {name}")


class TestIsSquashMerged:
    """The replay-and-cherry detection."""

    def test_detects_a_squash_merged_branch(self, repo: Repo) -> None:
        _branch_with_work(repo, "feature")
        _squash_merge(repo, "feature")

        assert is_squash_merged(Path(str(repo.working_dir)), "feature", "main") is True

    def test_unmerged_branch_is_not_reported(self, repo: Repo) -> None:
        _branch_with_work(repo, "feature")

        assert is_squash_merged(Path(str(repo.working_dir)), "feature", "main") is False

    def test_branch_with_extra_work_after_the_squash(self, repo: Repo) -> None:
        """Work added after the squash is not in main, so the branch must survive."""
        _branch_with_work(repo, "feature")
        _squash_merge(repo, "feature")
        repo.git.checkout("feature")
        _commit(repo, "later.txt", "later")
        repo.git.checkout("main")

        assert is_squash_merged(Path(str(repo.working_dir)), "feature", "main") is False

    def test_regular_merge_is_left_to_the_merged_check(self, repo: Repo) -> None:
        """A regularly merged branch is not found by this heuristic, by construction.

        Once the branch is an ancestor of main the merge base *is* the branch tip, so
        replaying its tree onto that base yields an empty patch and `git cherry` has
        nothing to match. These branches are caught by `git branch --merged` instead,
        which is why DeleteMode.ALL runs both checks.
        """
        _branch_with_work(repo, "feature")
        repo.git.merge("feature", "--no-ff", "-m", "merge")

        assert is_squash_merged(Path(str(repo.working_dir)), "feature", "main") is False


class TestFindCandidates:
    """Which branches are offered for deletion."""

    def test_main_is_never_a_candidate(self, repo: Repo) -> None:
        _branch_with_work(repo, "feature")
        _squash_merge(repo, "feature")

        names = [
            c.name
            for c in find_candidates(
                Path(str(repo.working_dir)), "main", DeleteMode.ALL
            )
        ]
        assert "main" not in names

    def test_squash_merged_branch_is_offered(self, repo: Repo) -> None:
        _branch_with_work(repo, "feature")
        _squash_merge(repo, "feature")

        candidates = find_candidates(
            Path(str(repo.working_dir)), "main", DeleteMode.ALL
        )
        assert Candidate("feature", MergeKind.SQUASH) in candidates

    def test_unmerged_branch_is_not_offered(self, repo: Repo) -> None:
        _branch_with_work(repo, "feature")

        names = [
            c.name
            for c in find_candidates(
                Path(str(repo.working_dir)), "main", DeleteMode.ALL
            )
        ]
        assert names == []

    def test_branch_checked_out_in_a_worktree_is_skipped(self, repo: Repo) -> None:
        """Git refuses to delete these, so offering them would guarantee a failure."""
        repo_path = Path(str(repo.working_dir))
        _branch_with_work(repo, "feature")
        _squash_merge(repo, "feature")
        run_git(["worktree", "add", str(repo_path.parent / "wt"), "feature"], repo_path)

        names = [c.name for c in find_candidates(repo_path, "main", DeleteMode.ALL)]
        assert "feature" not in names

    def test_squash_mode_skips_regular_merges(self, repo: Repo) -> None:
        repo_path = Path(str(repo.working_dir))
        repo.git.checkout("-b", "ancestor")
        repo.git.checkout("main")
        repo.git.merge("ancestor")

        names = [c.name for c in find_candidates(repo_path, "main", DeleteMode.MERGED)]
        assert "ancestor" in names

    def test_a_branch_is_offered_only_once(self, repo: Repo) -> None:
        """A regularly merged branch also passes the squash test; it must not
        duplicate."""
        repo_path = Path(str(repo.working_dir))
        _branch_with_work(repo, "feature")
        repo.git.merge("feature", "--no-ff", "-m", "merge")

        names = [c.name for c in find_candidates(repo_path, "main", DeleteMode.ALL)]
        assert names.count("feature") == 1


class TestCandidateForce:
    """Which git flag each kind needs."""

    def test_squash_merged_needs_force(self) -> None:
        """Git branch -d refuses a branch that is not an ancestor of main."""
        assert Candidate("x", MergeKind.SQUASH).force is True

    def test_regular_merge_does_not(self) -> None:
        assert Candidate("x", MergeKind.REGULAR).force is False
