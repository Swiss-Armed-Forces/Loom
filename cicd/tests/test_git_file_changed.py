"""Unit tests for the regeneration-loop safeguards, the push target and the patch.

The safeguard and patch tests build real git repositories rather than faking
git's output: the safeguards read history - what the previous commit touched,
and what the file looked like before it - and the patch is only correct if git
itself accepts it. Neither is reproduced faithfully by a test double.
"""

import os
from types import SimpleNamespace

import pytest
from git import Repo

from git_file_changed import (
    PushTarget,
    count_consecutive_ci_commits,
    generate_patch,
    get_oscillating_paths,
    resolve_push_target,
)

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
    Counting only one of them resets on every other commit, so a loop runs unnoticed.
    """
    _commit(repo, GENERATED, "C\n", CI_MESSAGE, "dev@example.com")
    _commit(repo, GENERATED, "D\n", CI_MESSAGE, "bot@noreply.example.com")

    assert count_consecutive_ci_commits(repo, ctx) == 3


def test_the_fork_patch_applies(repo, tmp_path):
    """A fork MR has no other way to pick up the regenerated files.

    The job prints `git apply <patch>` as the fix, so the patch has to survive a round
    trip through git rather than merely be written.
    """
    _write(repo, GENERATED, "C\n")
    ctx = SimpleNamespace(changed_out_dir=tmp_path / "artifacts", dry_run=False)

    patch_path = generate_patch(repo, ctx)

    repo.git.checkout("--", GENERATED)
    repo.git.apply(str(patch_path))
    with open(os.path.join(str(repo.working_dir), GENERATED), encoding="utf-8") as f:
        assert f.read() == "C\n"


def _mr_ctx(**overrides):
    """A fork MR context; override source_project_path to make it same-project."""
    fields = {
        "is_mr": True,
        "project_path": "upstream/loom",
        "source_project_path": "contributor/loom",
        "job_token": "job-token",
        "gitlab_token": "service-account-token",
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _refuse(_ctx):
    return False


def test_a_same_project_mr_pushes_with_the_job_token():
    """The job token's push rights are a setting on this project, which has them."""
    decision = resolve_push_target(
        _mr_ctx(source_project_path="upstream/loom"), _refuse
    )

    assert decision.target == PushTarget(
        project_path="upstream/loom", auth_user="gitlab-ci-token", token="job-token"
    )


def test_a_fork_allowing_collaboration_is_pushed_to_with_the_service_account():
    """The fork admits upstream members, which is what the service account is."""
    decision = resolve_push_target(_mr_ctx(), lambda _ctx: True)

    assert decision.target == PushTarget(
        project_path="contributor/loom",
        auth_user="oauth2",
        token="service-account-token",
    )


def test_a_fork_forbidding_collaboration_gets_a_patch():
    """The reason reaches the log the contributor reads, so it must name the setting."""
    decision = resolve_push_target(_mr_ctx(), _refuse)

    assert decision.target is None
    assert "upstream members" in decision.blocked_reason


def test_a_fork_is_not_asked_about_without_a_token():
    """Nothing can push without it, so the API call is waste."""

    def _explode(_ctx):
        raise AssertionError("allow_collaboration must not be read")

    decision = resolve_push_target(_mr_ctx(gitlab_token=None), _explode)

    assert decision.target is None
