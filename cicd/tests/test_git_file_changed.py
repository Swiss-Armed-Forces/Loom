"""Unit tests for the safeguards that stop a regeneration loop.

These build real git repositories rather than faking git's output: both
safeguards read history - what the previous commit touched, and what the file
looked like before it - which no test double reproduces faithfully.
"""

import os
from types import SimpleNamespace

import pytest
from git import Repo

from git_file_changed import count_consecutive_ci_commits, get_oscillating_paths

CI_MESSAGE = "chore(ci): update generated files from merge_request_event 1 (abc1234)"
GENERATED = "THIRD-PARTY.md"


def _configure(repo: Repo, hooks_path: str) -> None:
    """Pin the settings that make a repo behave the same on every developer machine.

    The temp repos live outside this worktree, so they inherit the developer's global
    git config: signing would open a pinentry dialog on every commit, and a global
    core.hooksPath would run the developer's hooks against these fixtures.
    """
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test")
    repo.git.config("commit.gpgsign", "false")
    repo.git.config("tag.gpgsign", "false")
    repo.git.config("core.hooksPath", hooks_path)


def _write(repo: Repo, path: str, content: str) -> None:
    full_path = os.path.join(str(repo.working_dir), path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)


def _commit(repo: Repo, path: str, content: str, message: str, email: str) -> None:
    _write(repo, path, content)
    repo.git.add("-A")
    repo.git.commit("-m", message, "--author", f"Someone <{email}>")


@pytest.fixture(name="ctx")
def fixture_ctx():
    """Only the commit prefix is consulted by the functions under test."""
    return SimpleNamespace(ci_commit_prefix="chore(ci):")


@pytest.fixture(name="repo")
def fixture_repo(tmp_path):
    """A repo whose HEAD is a CI commit that changed the generated file A -> B."""
    hooks_path = tmp_path / "no-hooks"
    hooks_path.mkdir()

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path, initial_branch="main")
    _configure(repo, str(hooks_path))

    _commit(repo, GENERATED, "A\n", "feat: initial", "dev@example.com")
    _commit(repo, GENERATED, "B\n", CI_MESSAGE, "bot@noreply.example.com")
    return repo


def test_generating_back_to_the_previous_content_is_flagged(repo, ctx):
    """A -> B -> A is the signature of a generator that answers per runner."""
    _write(repo, GENERATED, "A\n")

    assert get_oscillating_paths(repo, ctx, [GENERATED]) == [GENERATED]


def test_generating_new_content_is_not_flagged(repo, ctx):
    """A file may legitimately change twice running, as long as it advances.

    Committing one generated file can move the image tag another is derived from, so a
    second change is not by itself a loop.
    """
    _write(repo, GENERATED, "C\n")

    assert not get_oscillating_paths(repo, ctx, [GENERATED])


def test_nothing_is_flagged_when_head_is_not_a_ci_commit(repo, ctx):
    """The first regeneration after a developer's commit is the normal case."""
    _commit(repo, GENERATED, "A\n", "feat: a human commit", "dev@example.com")
    _write(repo, GENERATED, "B\n")

    assert not get_oscillating_paths(repo, ctx, [GENERATED])


def test_a_file_created_by_the_ci_commit_is_not_flagged(repo, ctx):
    """There is no earlier content to be generated back to."""
    _commit(repo, "THIRD-PARTY.lock", "1\n", CI_MESSAGE, "bot@noreply.example.com")
    _write(repo, "THIRD-PARTY.lock", "2\n")

    assert not get_oscillating_paths(repo, ctx, ["THIRD-PARTY.lock"])


def test_consecutive_ci_commits_are_counted_across_authors(repo, ctx):
    """Authorship must not break the chain.

    A commit is attributed to whoever's push or token started the pipeline, so a
    regeneration chain alternates between the developer and the pipeline-trigger bot.
    Counting only one of them resets on every other commit, which is how a loop once ran
    eight rounds unnoticed.
    """
    _commit(repo, GENERATED, "C\n", CI_MESSAGE, "dev@example.com")
    _commit(repo, GENERATED, "D\n", CI_MESSAGE, "bot@noreply.example.com")

    assert count_consecutive_ci_commits(repo, ctx) == 3
