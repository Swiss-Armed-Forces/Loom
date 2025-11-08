#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import git
import gitlab
from gitlab.v4.objects import ProjectMergeRequest, Project


# ----------------------------
# Config & context
# ----------------------------


@dataclass(frozen=True)
class CiContext:
    # Standard GitLab CI env vars
    api_url: str
    server_host: str
    project_id: int
    project_path: str
    job_token: Optional[str]
    pipeline_id: Optional[str]
    pipeline_source: Optional[str]
    commit_sha_short: Optional[str]

    # Source branch is only meaningful when running in an MR pipeline
    is_mr: bool
    source_branch: str  # empty when not MR

    # User-tunable (CLI-capable)
    project_access_token: Optional[str]
    mr_iid: Optional[str]
    author_name: str
    author_email: str
    add_skip_ci: bool
    log_level: str
    dry_run: bool
    max_ci_commits: int
    no_update: bool
    changed_out_dir: Path
    ci_commit_prefix: str = "chore(ci):"


def _req_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


def _truthy(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "on"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "In MR pipelines, stage ALL unstaged changes, commit & push to the MR "
            "source branch (with safeguards), then exit 1 if changes were detected. "
            "Uses CI_JOB_TOKEN for authentication. Optionally triggers new MR pipeline "
            "after successful push using PROJECT_ACCESS_TOKEN. "
            "In non-MR pipelines (or with --no-update), only verify cleanliness and "
            "fail if there are changes. Also copies changed files to a mirror folder."
        )
    )
    parser.add_argument(
        "--author-name",
        default=None,
        help="Commit author name (default: GITLAB_USER_NAME or 'CI Bot').",
    )
    parser.add_argument(
        "--author-email",
        default=None,
        help="Commit author email (default: GITLAB_USER_EMAIL or 'ci-bot@gitlab.local').",
    )
    parser.add_argument(
        "--project-access-token",
        default=None,
        help="Project access token for creating MR pipelines (default: PROJECT_ACCESS_TOKEN env var).",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="GitLab project ID (default: CI_PROJECT_ID env var).",
    )
    parser.add_argument(
        "--skip-ci",
        dest="add_skip_ci",
        action="store_true",
        default=None,
        help="Append [skip ci] to the commit message.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging level (default: LOG_LEVEL env or INFO).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only; do not stage/commit/push.",
    )
    parser.add_argument(
        "--max-ci-commits",
        type=int,
        default=int(os.getenv("MAX_CI_COMMITS", "10")),
        help="Abort if there are already this many consecutive CI commits. Default 10.",
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Verification-only mode: just check for unstaged changes and exit 1 if any; "
        "do not stage/commit/push even in MR pipelines.",
    )
    parser.add_argument(
        "--changed-out-dir",
        default=os.getenv("CHANGED_OUT_DIR", "changed-files"),
        help="Directory to mirror changed files into (preserving tree). "
        "Default: env CHANGED_OUT_DIR or 'changed-files'.",
    )
    return parser.parse_args(argv)


def build_context(ns: argparse.Namespace) -> CiContext:
    source_branch = os.getenv("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME", "")
    is_mr = bool(source_branch.strip())
    mr_iid = os.getenv("CI_MERGE_REQUEST_IID") if is_mr else None

    author_name = ns.author_name or os.getenv("GITLAB_USER_NAME", "CI Bot")
    author_email = ns.author_email or os.getenv(
        "GITLAB_USER_EMAIL", "ci-bot@gitlab.local"
    )

    if ns.add_skip_ci is None:
        add_skip_ci = _truthy(os.getenv("ADD_SKIP_CI", "0"))
    else:
        add_skip_ci = bool(ns.add_skip_ci)

    log_level = ns.log_level or os.getenv("LOG_LEVEL", "INFO")
    dry_run = bool(ns.dry_run or _truthy(os.getenv("DRY_RUN")))

    changed_out_dir = Path(ns.changed_out_dir).resolve()

    server_host = os.getenv("CI_SERVER_HOST", "gitlab.com")
    api_url = os.getenv("CI_API_V4_URL") or f"https://{server_host}/api/v4"

    return CiContext(
        api_url=api_url,
        server_host=server_host,
        project_id=ns.project_id or int(_req_env("CI_PROJECT_ID")),
        project_path=os.getenv("CI_PROJECT_PATH", "swiss-armed-forces/cyber-command/cea/loom"),
        job_token=os.getenv("CI_JOB_TOKEN"),
        pipeline_id=os.getenv("CI_PIPELINE_ID"),
        pipeline_source=os.getenv("CI_PIPELINE_SOURCE"),
        commit_sha_short=os.getenv("CI_COMMIT_SHORT_SHA"),
        is_mr=is_mr,
        source_branch=source_branch,
        project_access_token=ns.project_access_token
        or os.getenv("PROJECT_ACCESS_TOKEN"),
        mr_iid=mr_iid,
        author_name=author_name,
        author_email=author_email,
        add_skip_ci=add_skip_ci,
        log_level=log_level,
        dry_run=dry_run,
        max_ci_commits=ns.max_ci_commits,
        no_update=bool(ns.no_update),
        changed_out_dir=changed_out_dir,
    )


def setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(asctime)s %(levelname)s %(message)s")


# ----------------------------
# Git helpers
# ----------------------------


def init_git_repo(ctx: CiContext) -> git.Repo:
    """
    Prepare the repo safely for MR pushes.
      * set identity + safe.directory
      * set token remote
      * fetch origin/<source_branch>
      * checkout -B <branch> (align local branch)
      * pull --rebase with autostash to preserve local edits
    """
    repo = git.Repo(Path.cwd())

    if ctx.dry_run:
        logging.info("[DRY RUN] Would configure user/email and mark repo as safe.")
        logging.info("[DRY RUN] Would set remote 'origin' to CI_JOB_TOKEN auth URL.")
        logging.info("[DRY RUN] Would fetch origin/%s.", ctx.source_branch)
        logging.info("[DRY RUN] Would `checkout -B %s`.", ctx.source_branch)
        logging.info(
            "[DRY RUN] Would `git -c rebase.autostash=true pull --rebase origin %s`.",
            ctx.source_branch,
        )
        return repo

    with repo.config_writer() as cw:
        cw.set_value("user", "name", ctx.author_name)
        cw.set_value("user", "email", ctx.author_email)
        cw.set_value("safe", "directory", str(Path.cwd()))

    if ctx.job_token is not None:
        # Use CI job token for git operations
        https_url = (
            "https://gitlab-ci-token:"
            f"{ctx.job_token}@{ctx.server_host}/{ctx.project_path}.git"
        )
        logging.info("Using CI job token authentication")
    else:
        raise RuntimeError("No authentication provided: CI_JOB_TOKEN is required.")

    try:
        _ = repo.remotes.origin
    except AttributeError:
        repo.create_remote("origin", https_url)
    else:
        repo.remotes.origin.set_url(https_url)

    repo.git.fetch("--no-tags", "origin", ctx.source_branch, "--prune")
    repo.git.checkout("-B", ctx.source_branch)

    # autostash keeps any local uncommitted changes around the rebase
    repo.git.execute(
        [
            "git",
            "-c",
            "rebase.autostash=true",
            "pull",
            "--rebase",
            "origin",
            ctx.source_branch,
        ]
    )
    return repo


def get_unstaged_paths(repo: git.Repo) -> list[Path]:
    """
    Return paths with *unstaged* changes (tracked mods/deletes + untracked, not ignored).
    """
    paths: set[Path] = set()
    for diff in repo.index.diff(None):
        if diff.a_path:
            paths.add(Path(diff.a_path))
    for rel in repo.untracked_files:
        paths.add(Path(rel))
    return sorted(paths)


def print_paths(prefix: str, paths: Iterable[Path]) -> None:
    items = list(paths)
    if not items:
        logging.info("%s: none", prefix)
        return
    logging.info("%s (%d):", prefix, len(items))
    for p in items:
        logging.info("  %s", p)


def stage_all_unstaged(repo: git.Repo, ctx: CiContext) -> None:
    """Stage all working tree changes (equivalent to `git add --all`)."""
    if ctx.dry_run:
        logging.info("[DRY RUN] Would stage ALL unstaged changes: git add --all")
        return
    repo.git.add("--all")


def get_staged_names(repo: git.Repo) -> list[str]:
    """Return the list of staged file names (relative paths)."""
    out = repo.git.diff("--cached", "--name-only")
    return [line for line in out.splitlines() if line.strip()]


def has_staged_changes(repo: git.Repo) -> bool:
    """True if anything is staged relative to HEAD (works on first commit)."""
    if repo.head.is_valid():
        if repo.index.diff("HEAD"):
            return True
    return bool(repo.git.diff("--cached"))


# ----------------------------
# Copy changed files (preserve tree)
# ----------------------------
def copy_changed_files(
    repo: git.Repo,
    changed_paths: Iterable[Path],
    ctx: CiContext,
) -> None:
    """
    Copy all existing changed files into dest_root, preserving tree relative to repo root.
    Skips deleted/non-existent files (logs them).
    """
    wt = Path(repo.working_tree_dir or ".").resolve()

    items = list(changed_paths)
    if not items:
        logging.info("No changed files to copy.")
        return

    logging.info("Mirroring %d changed file(s) to: %s", len(items), ctx.changed_out_dir)
    for rel_path in items:
        src = wt / rel_path
        dst = ctx.changed_out_dir / rel_path
        if not src.exists():
            logging.info("Skipping (deleted/missing): %s", rel_path)
            continue
        if ctx.dry_run:
            logging.info("[DRY RUN] Would copy %s -> %s", src, dst)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


# ----------------------------
# Safeguards
# ----------------------------


def count_consecutive_ci_commits(
    repo: git.Repo, ctx: CiContext, limit: int = 50
) -> int:
    """
    Count consecutive commits from HEAD backwards that look like CI commits from this bot.
    """
    count = 0
    for commit in repo.iter_commits(max_count=limit):
        msg = commit.message or ""
        if not isinstance(msg, str):
            raise RuntimeError(f"Unexpected commit message type: '{type(msg)}'")
        email = (commit.author.email or "").lower()
        if msg.startswith(ctx.ci_commit_prefix) and email == ctx.author_email.lower():
            count += 1
        else:
            break
    return count


# ----------------------------
# Pipeline triggering
# ----------------------------


def wait_for_mr_commit_sync(
    project: Project,
    mr_iid: str,
    expected_commit_sha: str,
    max_retries: int = 5,
    base_delay: float = 2.0,
) -> bool:
    """
    Wait for GitLab MR to sync with the latest commit using exponential backoff.

    Args:
        project: GitLab project instance
        mr_iid: Merge request IID
        expected_commit_sha: The commit SHA we expect the MR to have
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds for exponential backoff (default: 2.0)

    Returns:
        True if MR synced successfully, False if timed out
    """
    for attempt in range(max_retries + 1):
        # Always fetch fresh MR data from API
        mr = project.mergerequests.get(mr_iid, lazy=True)
        diffs = mr.diffs.list()
        current_sha = None
        if diffs:
            # Get the latest diff (most recent)
            latest_diff = diffs[0]
            current_sha: str | None = latest_diff.head_commit_sha

        if current_sha == expected_commit_sha:
            if attempt > 0:
                logging.info("MR commit sync successful after %d attempt(s)", attempt)
            return True

        if attempt < max_retries:
            delay = base_delay * (2**attempt)  # Exponential backoff
            logging.info(
                "MR has commit %s, waiting for %s. Retrying in %.1fs (attempt %d/%d)",
                current_sha[:8] if current_sha else "unknown",
                expected_commit_sha[:8],
                delay,
                attempt + 1,
                max_retries,
            )
            time.sleep(delay)

    logging.error(
        "MR commit sync timeout after %d attempts. MR may have stale commit.",
        max_retries,
    )
    return False


def trigger_pipeline(ctx: CiContext) -> None:
    """
    Trigger a new merge request pipeline using the project access token.
    Waits for GitLab to sync the latest commit before triggering.
    No-ops in dry-run or if not in MR context or no token provided.
    """
    if not ctx.is_mr:
        logging.info("Not in MR context; skipping pipeline trigger.")
        return

    if not ctx.project_access_token:
        logging.info("No project access token provided; skipping pipeline trigger.")
        return

    if not ctx.mr_iid:
        logging.warning(
            "CI_MERGE_REQUEST_IID not available; skipping pipeline trigger."
        )
        return

    if ctx.dry_run:
        logging.info("[DRY RUN] Would trigger new MR pipeline for MR !%s", ctx.mr_iid)
        return

    # Create GitLab client and get merge request
    base_url = f"https://{ctx.server_host}"
    gl = gitlab.Gitlab(base_url, private_token=ctx.project_access_token)
    project = gl.projects.get(ctx.project_id, lazy=True)
    mr = project.mergerequests.get(ctx.mr_iid, lazy=True)

    # Get the latest commit SHA from the local repository
    repo = git.Repo(Path.cwd())
    latest_commit_sha = repo.head.commit.hexsha
    logging.info("Latest local commit: %s", latest_commit_sha[:8])

    # Wait for GitLab MR to sync with the latest commit
    logging.info("Waiting for MR !%s to sync with latest commit...", ctx.mr_iid)
    if not wait_for_mr_commit_sync(project, ctx.mr_iid, latest_commit_sha):
        logging.error(
            "Failed to sync MR with latest commit. Not triggering pipeline to avoid running on stale commit."
        )
        return

    # Create merge request pipeline using the MR pipeline API
    pipeline = mr.pipelines.create({})
    logging.info("Successfully triggered new MR pipeline: %s", pipeline.id)


# ----------------------------
# Committing & pushing
# ----------------------------


def commit_and_push(repo: git.Repo, ctx: CiContext) -> None:
    """
    Commit staged changes and push to the MR source branch.
    No-ops in dry-run.
    """
    msg = (
        f"{ctx.ci_commit_prefix} update generated files from "
        f"{ctx.pipeline_source or 'pipeline'} {ctx.pipeline_id or ''} "
        f"({ctx.commit_sha_short or ''})"
    )
    if ctx.add_skip_ci:
        msg += " [skip ci]"

    if ctx.dry_run:
        logging.info("[DRY RUN] Would commit with message:\n%s", msg.strip())
        logging.info("[DRY RUN] Would push HEAD:%s", ctx.source_branch)
        logging.info(
            "[DRY RUN] Would trigger new MR pipeline if project access token provided"
        )
        return

    if not has_staged_changes(repo):
        logging.info("No staged changes; nothing to commit.")
        return

    repo.index.commit(msg)
    logging.info("Committed staged changes.")
    repo.git.push("origin", f"HEAD:{ctx.source_branch}")
    logging.info("Pushed changes to origin/%s", ctx.source_branch)


# ----------------------------
# Main
# ----------------------------


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    ctx = build_context(ns)
    setup_logging(ctx.log_level)

    # Effective mode:
    # - update_mode = True only when in MR AND --no-update is NOT set
    update_mode = ctx.is_mr and not ctx.no_update
    mode = (
        "MR-update"
        if update_mode
        else ("verification-only (no-update)" if ctx.no_update else "non-MR")
    )
    logging.info("Running in %s mode for project %s", mode, ctx.project_path)

    repo = git.Repo(Path.cwd())

    # Detect and print all unstaged changes
    unstaged_before = get_unstaged_paths(repo)
    print_paths("Unstaged changes", unstaged_before)

    # Mirror changed files (preserve tree) to ctx.changed_out_dir
    copy_changed_files(repo, unstaged_before, ctx)

    if not update_mode:
        # Verification-only: do not modify the repo regardless of MR status.
        if not unstaged_before:
            logging.info("No changes detected. Nothing to do.")
            return 0
        logging.error(
            "Verification-only: changes detected (%d file(s)). Failing without updates.",
            len(unstaged_before),
        )
        return 1

    # From here: MR update mode (allowed to modify/push)

    if not unstaged_before:
        logging.info("No changes detected. Nothing to do.")
        return 0

    # Max consecutive CI commits safeguard
    consecutive = count_consecutive_ci_commits(repo, ctx)
    if consecutive >= ctx.max_ci_commits:
        logging.error(
            "Detected %d consecutive CI commits (>= %d). Aborting push to avoid a loop.",
            consecutive,
            ctx.max_ci_commits,
        )
        return 1

    # Prepare repo (fetch/checkout/pull with autostash)
    repo = init_git_repo(ctx)

    # Stage, list, commit, push
    stage_all_unstaged(repo, ctx)
    staged_now = (
        get_staged_names(repo) if not ctx.dry_run else [str(p) for p in unstaged_before]
    )
    print_paths("Files to push", [Path(p) for p in staged_now])

    commit_and_push(repo, ctx)

    # Trigger new pipeline after successful push
    trigger_pipeline(ctx)

    # Changes were present -> fail the job (even after push)
    logging.error("Changes were present and have been pushed. Failing the job.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
