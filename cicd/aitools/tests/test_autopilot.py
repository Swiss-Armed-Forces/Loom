"""Unit tests for detecting whether the implementation agent did any work.

Whether work happened is a question for git, not for the agent's exit code: the agent
can exit 0 having changed nothing, and it can push its own commits before exiting.
"""

from pathlib import Path
from typing import NamedTuple

import pytest
from git import Repo

from aitools.autopilot import _run_implement_agent
from aitools.models import AgentRun, BranchWorktree

BRANCH = "461-autopilot"


def _configure(repo: Repo, hooks_path: Path) -> None:
    with repo.config_writer() as writer:
        writer.set_value("user", "email", "tests@example.com")
        writer.set_value("user", "name", "aitools tests")
        writer.set_value("commit", "gpgsign", "false")
        writer.set_value("core", "hooksPath", str(hooks_path))


class _Issue(NamedTuple):
    """The handful of issue attributes the implement prompt and context file read."""

    iid: int = 461
    title: str = "Do the thing"
    description: str = "The thing needs doing."
    web_url: str = "https://example.invalid/-/issues/461"
    labels: list[str] = []


def _agent_run(ok: bool = True) -> AgentRun:
    return AgentRun(
        ok=ok,
        exit_code=0 if ok else 1,
        duration_s=0.1,
        turns=1,
        transcript_path="/dev/null",
        error="" if ok else "backend exited 1",
    )


@pytest.fixture(name="worktree")
def fixture_worktree(tmp_path):
    """A real repository standing in for a branch's dedicated checkout."""
    hooks_path = tmp_path / "no-hooks"
    hooks_path.mkdir()

    upstream_path = tmp_path / "upstream"
    upstream = Repo.init(upstream_path, initial_branch=BRANCH)
    _configure(upstream, hooks_path)
    upstream.git.config("receive.denyCurrentBranch", "ignore")
    (upstream_path / "README.md").write_text("base\n", encoding="utf-8")
    upstream.git.add("-A")
    upstream.git.commit("-m", "initial")

    work_path = tmp_path / "work"
    work = Repo.clone_from(str(upstream_path), str(work_path))
    _configure(work, hooks_path)

    return BranchWorktree(
        repo=work,
        path=str(work_path),
        branch=BRANCH,
        created=True,
        in_place=False,
    )


class TestRunImplementAgent:
    def test_an_agent_that_changes_nothing_reports_no_commit(self, worktree):
        def change_nothing(_prompt, _worktree, _label):
            return _agent_run()

        attempt = _run_implement_agent(_Issue(), worktree, change_nothing)

        assert attempt.committed is False
        assert attempt.detail

    def test_an_agent_that_pushed_its_own_commit_still_counts_as_work(self, worktree):
        """The check compares against the sha before the run, not against origin.

        Comparing `origin/<branch>..HEAD` instead reports nothing whenever the agent
        pushed what it committed, which is what a prompt telling it to push produces.
        """

        def commit_and_push(_prompt, _worktree, _label):
            (Path(worktree.path) / "thing.py").write_text("done\n", encoding="utf-8")
            worktree.repo.git.add("-A")
            worktree.repo.git.commit("-m", "feat(core): do the thing")
            worktree.repo.git.push("origin", BRANCH)
            return _agent_run()

        attempt = _run_implement_agent(_Issue(), worktree, commit_and_push)

        assert attempt.committed is True
        assert attempt.detail == ""
