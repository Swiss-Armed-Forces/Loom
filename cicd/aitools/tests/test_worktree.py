"""Unit tests for branch worktree acquisition.

These build real git repositories rather than faking git's output: what is under test is
git's own worktree model — which checkout holds a branch, and what `git worktree add`
refuses — and no test double reproduces that faithfully.
"""

import os
from pathlib import Path

import pytest
from git import Repo

from aitools.worktree import acquire_branch_worktree

BRANCH = "feature/slashed"
# Worktrees are added beside the primary checkout, so naming the clone pins where they
# land without any configuration: <tmp_path>/loom-worktrees/<branch>.
CHECKOUT_NAME = "loom"


def _configure(repo: Repo, hooks_path: Path) -> None:
    """Pin the repo's identity and disable anything the developer's config would add."""
    with repo.config_writer() as writer:
        writer.set_value("user", "email", "tests@example.com")
        writer.set_value("user", "name", "aitools tests")
        writer.set_value("commit", "gpgsign", "false")
        writer.set_value("tag", "gpgsign", "false")
        writer.set_value("core", "hooksPath", str(hooks_path))


@pytest.fixture(name="clone")
def fixture_clone(tmp_path):
    """A clone whose "origin" is a real sibling repository.

    Acquisition fetches origin and adds worktrees beside the primary checkout, so the
    tests need a real remote and a clone that is alone in its directory.
    """
    hooks_path = tmp_path / "no-hooks"
    hooks_path.mkdir()

    upstream_path = tmp_path / "upstream"
    upstream = Repo.init(upstream_path, initial_branch="main")
    _configure(upstream, hooks_path)
    upstream.git.config("receive.denyCurrentBranch", "ignore")
    (upstream_path / "README.md").write_text("base\n", encoding="utf-8")
    upstream.git.add("-A")
    upstream.git.commit("-m", "initial")
    upstream.git.checkout("-b", BRANCH)
    (upstream_path / "feature.txt").write_text("feature\n", encoding="utf-8")
    upstream.git.add("-A")
    upstream.git.commit("-m", "feature")
    upstream.git.checkout("main")

    clone_path = tmp_path / CHECKOUT_NAME
    clone = Repo.clone_from(str(upstream_path), str(clone_path))
    _configure(clone, hooks_path)
    return clone


class TestAcquireBranchWorktree:
    def test_remote_branch_gets_its_own_worktree(self, clone, tmp_path):
        """A branch that exists only on origin is checked out beside the clone."""
        acquired = acquire_branch_worktree(clone, BRANCH)

        assert acquired.created is True
        assert acquired.in_place is False
        # The branch name stays a nested path: flattening it would invent collisions
        # that git's own ref rules cannot produce.
        assert Path(acquired.path) == tmp_path / f"{CHECKOUT_NAME}-worktrees" / BRANCH
        assert acquired.repo.active_branch.name == BRANCH
        assert os.path.isfile(os.path.join(acquired.path, "feature.txt"))
        # The whole point: the invoking checkout never moves.
        assert clone.active_branch.name == "main"

    def test_second_acquisition_reuses_and_fast_forwards(self, clone, tmp_path):
        """An existing worktree is reused and brought up to its remote."""
        first = acquire_branch_worktree(clone, BRANCH)

        upstream = Repo(tmp_path / "upstream")
        upstream.git.checkout(BRANCH)
        (tmp_path / "upstream" / "later.txt").write_text("later\n", encoding="utf-8")
        upstream.git.add("-A")
        upstream.git.commit("-m", "later")
        upstream.git.checkout("main")

        second = acquire_branch_worktree(clone, BRANCH)

        assert second.path == first.path
        assert second.created is False
        assert os.path.isfile(os.path.join(second.path, "later.txt"))

    def test_branch_held_by_the_invoking_checkout_is_used_in_place(self, clone):
        """Git cannot check a branch out twice, so the invoking tree serves itself."""
        clone.git.checkout("-b", BRANCH, f"origin/{BRANCH}")

        acquired = acquire_branch_worktree(clone, BRANCH)

        assert acquired.in_place is True
        assert acquired.path == str(Path(clone.working_dir).resolve())

    def test_dirty_worktree_keeps_its_changes(self, clone, tmp_path):
        """Uncommitted work in an acquired worktree survives a later acquisition."""
        first = acquire_branch_worktree(clone, BRANCH)
        scratch = Path(first.path) / "wip.txt"
        scratch.write_text("unsaved\n", encoding="utf-8")
        head_before = first.repo.head.commit.hexsha

        upstream = Repo(tmp_path / "upstream")
        upstream.git.checkout(BRANCH)
        (tmp_path / "upstream" / "later.txt").write_text("later\n", encoding="utf-8")
        upstream.git.add("-A")
        upstream.git.commit("-m", "later")
        upstream.git.checkout("main")

        second = acquire_branch_worktree(clone, BRANCH)

        assert scratch.read_text(encoding="utf-8") == "unsaved\n"
        assert second.repo.head.commit.hexsha == head_before
