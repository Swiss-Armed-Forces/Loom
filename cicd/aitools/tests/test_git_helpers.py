"""Unit tests for branch diff range resolution.

These build real git repositories rather than faking git's output: the behaviour under
test lives in git's own history model (a branch that has merged its target in has more
than one merge base), which no test double reproduces faithfully.
"""

import logging
import os
import subprocess

import pytest
from git import Repo

from aitools.git_helpers import get_branch_diff, get_per_file_diffs, resolve_diff_range
from aitools.prompts import build_diff_caveats, build_discovery_command

TARGET = "main"
TARGET_REF = f"origin/{TARGET}"


def _commit(repo: Repo, path: str, content: str, message: str) -> str:
    """Write a file, commit it, and return the commit sha."""
    full_path = os.path.join(str(repo.working_dir), path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    repo.git.add("-A")
    repo.git.commit("-m", message)
    return repo.head.commit.hexsha


def _configure(repo: Repo, hooks_path: str) -> None:
    """Pin the settings that make a repo behave the same on every developer machine.

    The temp repos live outside this worktree, so they inherit the developer's global
    git config: signing would open a pinentry dialog on every commit and merge, and a
    global core.hooksPath would run the developer's hooks against these fixtures.
    """
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test")
    repo.git.config("commit.gpgsign", "false")
    repo.git.config("tag.gpgsign", "false")
    repo.git.config("core.hooksPath", hooks_path)


@pytest.fixture(name="origin_repo")
def fixture_origin_repo(tmp_path):
    """A clone whose "origin" is a real sibling repository.

    resolve_diff_range fetches origin and diffs against origin/<target>, so the tests
    need a remote rather than a single standalone repo.
    """
    hooks_path = tmp_path / "no-hooks"
    hooks_path.mkdir()

    upstream_path = tmp_path / "upstream"
    upstream_path.mkdir()
    upstream = Repo.init(upstream_path, initial_branch=TARGET)
    _configure(upstream, str(hooks_path))
    # The tests push to this repo while it has TARGET checked out; without this git
    # refuses the push rather than updating a branch under its own working tree.
    upstream.git.config("receive.denyCurrentBranch", "ignore")
    _commit(upstream, "base.txt", "base\n", "initial")

    clone_path = tmp_path / "clone"
    clone = Repo.clone_from(str(upstream_path), str(clone_path))
    _configure(clone, str(hooks_path))
    return clone


@pytest.fixture(name="feature_repo")
def fixture_feature_repo(origin_repo):
    """An origin_repo sitting on a "feature" branch with one commit of its own."""
    origin_repo.git.checkout("-b", "feature")
    _commit(origin_repo, "feature.txt", "mine\n", "feat: add feature")
    return origin_repo


def _advance_target(repo: Repo, path: str, content: str, message: str) -> None:
    """Add a commit to the target branch on origin and refresh the tracking ref."""
    current = repo.active_branch.name
    repo.git.checkout(TARGET)
    repo.git.pull("origin", TARGET)
    _commit(repo, path, content, message)
    repo.git.push("origin", TARGET)
    repo.git.checkout(current)


def _make_conflict(repo: Repo) -> None:
    """Leave the repo on a "feature" branch that no longer merges into the target."""
    repo.git.checkout("-b", "feature")
    _commit(repo, "contested.txt", "branch version\n", "feat: our take")
    _advance_target(repo, "contested.txt", "target version\n", "feat: their take")


def _make_criss_cross(repo: Repo) -> None:
    """Leave the repo on a "feature" branch that has two merge bases with the target.

    Two bases need a commit that reaches the target and the branch by different routes.
    This mirrors what happens in practice: a branch merges the target in, picks up a
    sibling branch's commit directly, and the target then merges that sibling itself.
    Afterwards neither "target work" nor "other work" is an ancestor of the other, so
    `git merge-base` has two equally valid answers and returns an arbitrary one.
    """
    repo.git.checkout("-b", "other")
    _commit(repo, "other.txt", "theirs\n", "feat: other work")

    repo.git.checkout(TARGET)
    repo.git.checkout("-b", "feature")
    _commit(repo, "feature.txt", "mine\n", "feat: mine")

    _advance_target(repo, "target.txt", "target\n", "feat: target work")
    repo.git.merge(TARGET_REF, "--no-edit")
    repo.git.merge("other", "--no-edit")

    repo.git.checkout(TARGET)
    repo.git.merge("--no-ff", "other", "-m", f"Merge branch 'other' into '{TARGET}'")
    repo.git.push("origin", TARGET)
    repo.git.checkout("feature")


class TestResolveDiffRange:
    def test_linear_branch_reports_only_its_own_files(self, feature_repo):
        """A branch with a single merge base reports only its own files."""
        diff_range = resolve_diff_range(feature_repo, "HEAD", TARGET)
        files = feature_repo.git.diff(
            diff_range.left, diff_range.right, "--name-only"
        ).split()

        assert diff_range.strategy == "merge-tree"
        assert diff_range.behind_count == 0
        assert files == ["feature.txt"]

    def test_criss_cross_history_excludes_work_the_branch_did_not_make(
        self, origin_repo
    ):
        """A branch with two merge bases must still report only its own files.

        Diffing from a merge base reports whichever side git's arbitrary choice of base
        puts behind HEAD — in this history, the sibling branch's other.txt, which the
        target already carries.
        """
        _make_criss_cross(origin_repo)
        assert len(origin_repo.git.merge_base("--all", TARGET_REF, "HEAD").split()) == 2

        diff_range = resolve_diff_range(origin_repo, "HEAD", TARGET)
        files = origin_repo.git.diff(
            diff_range.left, diff_range.right, "--name-only"
        ).split()

        assert files == ["feature.txt"]

    def test_behind_count_counts_unmerged_target_commits(self, feature_repo):
        _advance_target(feature_repo, "their_first.txt", "theirs\n", "feat: theirs")
        _advance_target(feature_repo, "their_second.txt", "more\n", "feat: theirs too")

        assert resolve_diff_range(feature_repo, "HEAD", TARGET).behind_count == 2

    def test_conflicting_branch_falls_back_to_merge_base(self, origin_repo, caplog):
        """A branch that cannot merge still yields a diff, with a warning."""
        _make_conflict(origin_repo)

        with caplog.at_level(logging.WARNING):
            diff_range = resolve_diff_range(origin_repo, "HEAD", TARGET)

        assert diff_range.strategy == "merge-base"
        assert diff_range.right == "HEAD"
        assert "mr-update" in caplog.text
        assert origin_repo.git.diff(diff_range.left, diff_range.right, "--name-only")

    def test_unrelated_history_raises_instead_of_crashing_in_the_fallback(
        self, origin_repo
    ):
        """An orphan branch shares no merge base, so the fallback cannot degrade."""
        origin_repo.git.checkout("--orphan", "feature")
        origin_repo.git.rm("-rf", ".")
        _commit(origin_repo, "feature.txt", "mine\n", "feat: add feature")

        with pytest.raises(RuntimeError, match="No common history"):
            resolve_diff_range(origin_repo, "HEAD", TARGET)


class TestDiscoveryCommand:
    def test_command_reproduces_the_range(self, origin_repo):
        _make_criss_cross(origin_repo)
        diff_range = resolve_diff_range(origin_repo, "HEAD", TARGET)

        out = subprocess.run(
            build_discovery_command(diff_range),
            shell=True,
            cwd=origin_repo.working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        assert out.stdout.split() == ["feature.txt"]

    def test_command_applies_the_same_exclusions_as_the_diff(self, feature_repo):
        """branch.diff drops lockfiles, so the agent's file list must drop them too."""
        _commit(feature_repo, "backend/common/poetry.lock", "lock\n", "chore: lock")
        diff_range = resolve_diff_range(feature_repo, "HEAD", TARGET)

        out = subprocess.run(
            build_discovery_command(diff_range),
            shell=True,
            cwd=feature_repo.working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        assert out.stdout.split() == ["feature.txt"]
        assert "poetry.lock" not in get_branch_diff(
            feature_repo, "HEAD", TARGET, diff_range=diff_range
        )


class TestDiffCaveats:
    def test_no_caveats_when_the_branch_is_current_and_checked_out(self, feature_repo):
        diff_range = resolve_diff_range(feature_repo, "HEAD", TARGET)

        assert not build_diff_caveats(diff_range, TARGET)

    def test_behind_caveat_reports_how_far_behind_the_branch_is(self, feature_repo):
        _advance_target(feature_repo, "their_first.txt", "theirs\n", "feat: theirs")
        diff_range = resolve_diff_range(feature_repo, "HEAD", TARGET)

        caveats = build_diff_caveats(diff_range, TARGET)

        assert len(caveats) == 1
        assert "1 commit(s) behind" in caveats[0]

    def test_merge_base_fallback_replaces_the_behind_caveat(self, origin_repo):
        """On the fallback the diff ends at HEAD, so "older than the diff" is wrong."""
        _make_conflict(origin_repo)
        diff_range = resolve_diff_range(origin_repo, "HEAD", TARGET)

        caveats = build_diff_caveats(diff_range, TARGET)

        assert len(caveats) == 1
        assert "arbitrary merge base" in caveats[0]
        assert "older than the diff" not in caveats[0]

    def test_caveat_warns_when_the_branch_is_not_checked_out(self, origin_repo):
        _make_conflict(origin_repo)
        origin_repo.git.push("origin", "feature")
        origin_repo.git.checkout(TARGET)

        diff_range = resolve_diff_range(origin_repo, "origin/feature", TARGET)
        caveats = build_diff_caveats(diff_range, TARGET)

        assert any("git show origin/feature:<path>" in c for c in caveats)


class TestBranchDiff:
    def test_diff_carries_no_prose_before_the_stat_summary(self, feature_repo):
        """Callers feed this straight into prompts; prose here leaks into MR text."""
        _advance_target(feature_repo, "their_first.txt", "theirs\n", "feat: theirs")

        assert get_branch_diff(feature_repo, "HEAD", TARGET).startswith(
            "Changed files:"
        )


class TestPerFileDiffs:
    def test_criss_cross_history_excludes_work_the_branch_did_not_make(
        self, origin_repo
    ):
        """get_per_file_diffs resolves the range the same way as get_branch_diff."""
        _make_criss_cross(origin_repo)

        result = get_per_file_diffs(origin_repo, TARGET)

        assert list(result.files) == ["feature.txt"]
