import argparse
import logging
import os
import sys
import tempfile

import gitlab
from git import Repo
from git.exc import GitCommandError
from gitlab.v4.objects import Project, ProjectMergeRequest, ProjectPipeline

from . import config
from .aitools import (
    generate_commit_message_via_ai,
    parse_commit_message,
    run_agent,
)
from .git_helpers import get_branch_diff, load_mr_template
from .gitlab_api import (
    extract_job_artifacts,
    fetch_first_failing_job,
    fetch_job_log,
    fetch_mr_by_ref,
    find_open_mr_for_branch,
    get_gitlab_client,
    parse_mr_url_or_id,
    update_mr,
)
from .models import BranchWorktree, CommitMessage, FixRoundResult, MRContext
from .prompts import build_watch_fix_prompt
from .worktree import acquire_branch_worktree

logger = logging.getLogger(__name__)


def acquire_mr_worktree(mr: ProjectMergeRequest, repo: Repo) -> BranchWorktree:
    """Return the checkout dedicated to the MR's source branch."""
    return acquire_branch_worktree(repo, mr.source_branch)


def _ask(prompt: str) -> str:
    """Prompt the user for input, or take the default when nobody can answer.

    An unattended run reaches these prompts with no terminal behind it, where `input()`
    would block until the process is killed.
    """
    if config.AUTO_MODE:
        print(f"{prompt}y (auto)")
        return "y"
    if not sys.stdin.isatty():
        print(f"{prompt}y (no terminal)")
        return "y"
    return input(prompt).strip().lower()


def fix_failing_job_and_push(
    project: Project, pipeline: ProjectPipeline, worktree: BranchWorktree
) -> FixRoundResult:
    """Diagnose the first failing job via AI and push whatever it commits."""
    job = fetch_first_failing_job(project, pipeline)
    if not job:
        print("Pipeline failed but no failing job found.")
        return FixRoundResult(job_id=None, commits_pushed=0, pushed=False)

    print(f"\nFailing job: #{job.id} '{job.name}' (stage: {job.stage})")

    log = fetch_job_log(job)
    with tempfile.TemporaryDirectory(prefix=".loom_watch_", dir=worktree.path) as ctx:
        with open(os.path.join(ctx, "job_log.txt"), "w", encoding="utf-8") as f:
            f.write(log)
        artifacts_dir = os.path.join(ctx, "artifacts")
        os.makedirs(artifacts_dir)
        extract_job_artifacts(job, artifacts_dir)
        run = run_agent(build_watch_fix_prompt(job, ctx, pipeline.id), worktree, "fix")

    if not run.ok:
        logger.warning("Fix agent failed: %s", run.error)

    # A failed run is still worth harvesting: the agent may have committed before dying.
    try:
        ahead = list(worktree.repo.iter_commits(f"origin/{worktree.branch}..HEAD"))
    except GitCommandError:
        ahead = []

    if not ahead:
        print("No commits made.")
        return FixRoundResult(job_id=job.id, commits_pushed=0, pushed=False)

    worktree.repo.git.push("origin", worktree.branch)
    print(f"Pushed {len(ahead)} commit(s) to {worktree.branch}")
    return FixRoundResult(job_id=job.id, commits_pushed=len(ahead), pushed=True)


def resolve_mr_from_args_or_branch(
    gl: gitlab.Gitlab, args: argparse.Namespace, repo: Repo
) -> ProjectMergeRequest:
    """Resolve the target MR: explicit URL/IID from args, or the MR for the current
    branch.

    Handles detached HEAD state with a clear error message directing the user to pass
    the MR reference explicitly.
    """
    if args.mr:
        try:
            ref = parse_mr_url_or_id(args.mr)
        except ValueError as e:
            logger.error("%s", e)
            sys.exit(1)
        return fetch_mr_by_ref(gl, repo, ref)
    if repo.head.is_detached:
        logger.error(
            "Detached HEAD: cannot determine current branch. Pass --mr explicitly."
        )
        sys.exit(1)
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)
    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)
    logger.info("Found MR !%s: %s", mr.iid, mr.title)
    return mr


def _get_gitlab_client_or_exit() -> gitlab.Gitlab:
    """Return a GitLab client or exit with an error message."""
    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)
    return gl


def _get_mr_for_current_branch(repo: Repo) -> ProjectMergeRequest:
    """Return the open MR for the current branch, or exit with an error."""
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)
    gl = _get_gitlab_client_or_exit()
    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)
    logger.info("Found MR !%s: %s", mr.iid, mr.title)
    return mr


def generate_mr_description(
    mr: ProjectMergeRequest,
    repo: Repo,
) -> CommitMessage | None:
    """Generate a new MR title and description from the branch diff."""
    diff = get_branch_diff(repo, target_branch=mr.target_branch)
    mr_template = load_mr_template(repo)
    message = generate_commit_message_via_ai(
        diff,
        mr_template,
        repo,
        MRContext(title=mr.title, description=mr.description or ""),
        mr.target_branch,
    )
    if not message:
        logger.warning("Could not generate MR description for !%s — skipping", mr.iid)
        return None
    return parse_commit_message(message)


def _maybe_update_mr_description(
    mr: ProjectMergeRequest,
    repo: Repo,
) -> None:
    """Generate a new MR title/description via AI and optionally apply it."""
    parsed = generate_mr_description(mr, repo)
    if not parsed:
        return
    print("\n--- MR Preview ---")
    print(f"Title: {parsed.title}\n")
    print(f"Description:\n{parsed.body}")
    print("--- End Preview ---\n")
    answer = _ask(f"Update MR !{mr.iid} description? [Y/n]: ")
    if answer in ("", "y"):
        update_mr(mr, parsed.title, parsed.body)
        logger.info("Updated MR !%s", mr.iid)
