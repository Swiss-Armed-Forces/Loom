"""Acquisition of the checkout a subcommand does its work in.

Every subcommand that touches a branch works in a checkout dedicated to that branch, so
the invoking tree's HEAD is never moved under the user. The exception is `mr-create`,
whose input is uncommitted work that already lives in the invoking tree.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

from git import Repo
from git.exc import GitCommandError

from . import config
from .models import BranchWorktree, WorktreeEnvironment

logger = logging.getLogger(__name__)

LOCAL_SETTINGS_FILE = "devenv.local.nix"

# Entering devenv once is what gives a worktree its own .venv, its hooks path and a PATH
# resolving to its own sources. Until then every tool an agent runs there resolves to the
# primary checkout, so it lints and tests code that is not the code it just wrote. sova
_ENVIRONMENTS: dict[str, WorktreeEnvironment] = {}


def main_checkout(repo: Repo) -> Path:
    """The primary checkout's directory, from any of the repository's worktrees."""
    # git answers this relative to the repository when it can, so it has to be resolved
    # against the repository rather than against the process's own directory.
    common_dir = Path(repo.git.rev_parse("--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = Path(_resolve_path(repo)) / common_dir
    return common_dir.resolve().parent


def worktrees_root(repo: Repo) -> Path:
    """The directory branch worktrees are added under."""
    if config.WORKTREES_ROOT:
        return Path(config.WORKTREES_ROOT).expanduser().resolve()
    main = main_checkout(repo)
    return main.parent / f"{main.name}-worktrees"


def checkout_holding(repo: Repo, branch: str) -> Path | None:
    """The checkout that currently has `branch` checked out, if any.

    Git refuses to check a branch out in two worktrees at once, so this answers whether
    an acquisition has to create one or can reuse what is already there.
    """
    listing = repo.git.worktree("list", "--porcelain")
    path: Path | None = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :]).resolve()
        elif line.startswith("branch ") and path is not None:
            if line[len("branch ") :].strip() == f"refs/heads/{branch}":
                return path
    return None


def _resolve_path(repo: Repo) -> str:
    """The working directory of a checkout, as a plain string."""
    working_dir = repo.working_dir
    if not working_dir:
        raise RuntimeError("Repository has no working directory (bare repo?)")
    return str(Path(working_dir).resolve())


def current_checkout(repo: Repo, branch: str) -> BranchWorktree:
    """Describe the invoking checkout as the place the work happens."""
    return BranchWorktree(
        repo=repo,
        path=_resolve_path(repo),
        branch=branch,
        created=False,
        in_place=True,
    )


def _copy_local_settings(main: Path, target: Path) -> None:
    """Give a new worktree the gitignored local settings the tools need there.

    The file carries GITLAB_TOKEN, so a worktree without it fails every GitLab call. An
    existing file is never overwritten and its contents are never read or logged.
    """
    source = main / LOCAL_SETTINGS_FILE
    destination = target / LOCAL_SETTINGS_FILE
    if not source.is_file() or destination.exists():
        return
    shutil.copy2(source, destination)
    logger.info("Copied %s into %s", LOCAL_SETTINGS_FILE, target)


def _fast_forward(work: Repo, branch: str) -> None:
    """Bring an acquired checkout up to its remote tracking ref.

    A dirty checkout keeps its changes: the agent that left them there may still be the
    one being served.
    """
    if work.is_dirty(untracked_files=True):
        logger.warning("Working tree is dirty — skipping update to origin/%s", branch)
        return
    try:
        work.git.merge("--ff-only", f"origin/{branch}")
    except GitCommandError as e:
        logger.warning("Could not fast-forward %s to origin/%s: %s", branch, branch, e)


def _branch_exists(repo: Repo, ref: str) -> bool:
    try:
        repo.git.rev_parse("--verify", "--quiet", ref)
        return True
    except GitCommandError:
        return False


def _add_worktree(repo: Repo, branch: str, target: Path) -> None:
    """Add a worktree for `branch` at `target`."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if _branch_exists(repo, f"refs/heads/{branch}"):
        repo.git.worktree("add", str(target), branch)
        return
    if not _branch_exists(repo, f"refs/remotes/origin/{branch}"):
        raise RuntimeError(
            f"Branch {branch!r} exists neither locally nor on origin — "
            "create it before acquiring a worktree for it"
        )
    repo.git.worktree("add", "-b", branch, str(target), f"origin/{branch}")


def acquire_branch_worktree(repo: Repo, branch: str) -> BranchWorktree:
    """Return the checkout dedicated to `branch`, creating one when there is none.

    `repo` is only read: its refs are shared with every worktree of the repository, and
    its HEAD is never moved.
    """
    try:
        repo.git.fetch("origin", branch)
    except GitCommandError as e:
        logger.warning("Could not fetch origin/%s: %s", branch, e)

    held = checkout_holding(repo, branch)
    if held is not None:
        if held == Path(_resolve_path(repo)):
            logger.info("Branch %s is checked out here — working in place", branch)
            return current_checkout(repo, branch)
        logger.info("Reusing worktree %s for branch %s", held, branch)
        work = Repo(held)
        _fast_forward(work, branch)
        return BranchWorktree(
            repo=work,
            path=str(held),
            branch=branch,
            created=False,
            in_place=False,
        )

    # Clears admin entries whose directory was removed by hand, which otherwise make
    # `git worktree add` refuse the path as "missing but locked".
    repo.git.worktree("prune")

    target = worktrees_root(repo) / branch
    if target.exists():
        raise RuntimeError(
            f"{target} exists but is not a worktree of this repository. "
            f"Remove it with: git worktree remove {target}"
        )

    _add_worktree(repo, branch, target)
    _copy_local_settings(main_checkout(repo), target)
    work = Repo(target)
    _fast_forward(work, branch)
    logger.info("Added worktree %s for branch %s", target, branch)
    return BranchWorktree(
        repo=work,
        path=str(target),
        branch=branch,
        created=True,
        in_place=False,
    )


def _is_worktree_of(repo: Repo, path: str) -> bool:
    """Whether `path` is a registered worktree of this repository."""
    listing = repo.git.worktree("list", "--porcelain")
    resolved = Path(path).resolve()
    for line in listing.splitlines():
        if line.startswith("worktree ") and Path(line[len("worktree ") :]) == resolved:
            return True
    return False


def _build_environment(path: str) -> str:
    """Trust the directory and build its environment, reporting why it did not work.

    The first entry into a fresh worktree is a nix build, which is why this streams its
    output: a silent multi-minute wait is indistinguishable from a hang.
    """
    try:
        for argv in (
            ["direnv", "allow", path],
            ["direnv", "exec", path, "true"],
        ):
            result = subprocess.run(
                argv,
                cwd=path,
                timeout=config.DEVENV_BOOTSTRAP_TIMEOUT,
                check=False,
            )
            if result.returncode != 0:
                return f"{' '.join(argv)} exited {result.returncode}"
    except (subprocess.TimeoutExpired, OSError) as e:
        return str(e)
    return ""


def _enter_environment(worktree: BranchWorktree) -> WorktreeEnvironment:
    """Build the worktree's devenv environment and return the argv prefix entering
    it."""
    if config.SKIP_DEVENV:
        logger.warning(
            "AITOOLS_SKIP_DEVENV is set — running the agent outside devenv, so its "
            "tools resolve to whatever is on PATH"
        )
        return WorktreeEnvironment(ready=True, prefix=[], reason="")

    if worktree.in_place:
        return WorktreeEnvironment(ready=True, prefix=[], reason="")

    if not shutil.which("direnv"):
        return WorktreeEnvironment(
            ready=False,
            prefix=[],
            reason="direnv is not installed, so the worktree's environment cannot be "
            "entered (set AITOOLS_SKIP_DEVENV=1 where the environment is baked in)",
        )

    # direnv allow grants shell-execution trust to a directory, so it is only ever given
    # to a path git confirms is a worktree of the repository the command was run in.
    if not _is_worktree_of(worktree.repo, worktree.path):
        return WorktreeEnvironment(
            ready=False,
            prefix=[],
            reason=f"{worktree.path} is not a worktree of this repository",
        )

    logger.info("Entering the devenv environment in %s", worktree.path)
    failure = _build_environment(worktree.path)
    if failure:
        return WorktreeEnvironment(ready=False, prefix=[], reason=failure)

    return WorktreeEnvironment(
        ready=True,
        prefix=["direnv", "exec", worktree.path],
        reason="",
    )


def ensure_environment(worktree: BranchWorktree) -> WorktreeEnvironment:
    """Return how to run a command inside the worktree's own devenv environment.

    The result is memoised per path: entering is a nix build the first time and a cache
    lookup afterwards, and a command that never runs an agent should not pay for it.
    """
    cached = _ENVIRONMENTS.get(worktree.path)
    if cached is not None:
        return cached
    environment = _enter_environment(worktree)
    _ENVIRONMENTS[worktree.path] = environment
    return environment


def devenv_root(repo: Repo) -> str:
    """The directory a devenv-aware command is run from."""
    return str(main_checkout(repo))


def state_dir() -> Path:
    """The directory transcripts and strand logs are written to.

    Outside every checkout: an agent never reads them, they have to outlive the run, and
    a path inside a tree would depend on a .gitignore entry and enter build contexts.
    """
    if config.STATE_DIR:
        return Path(config.STATE_DIR).expanduser()
    base = os.getenv("XDG_STATE_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".local" / "state"
    return root / "loom"
