import argparse
import logging
import os
import sys
import tempfile
import time

import gitlab
from git import Repo
from git.exc import GitCommandError
from gitlab.v4.objects import Project, ProjectMergeRequest, ProjectPipeline

from ._common import _get_gitlab_client_or_exit, _maybe_update_mr_description
from .claude import run_claude_agentic
from .gitlab_api import (
    PIPELINE_WAITING_STATUSES,
    extract_job_artifacts,
    fetch_first_failing_job,
    fetch_job_log,
    fetch_latest_pipeline_for_mr,
    fetch_mr_by_ref,
    fetch_watched_mrs,
    find_open_mr_for_branch,
    get_project,
    parse_mr_url_or_id,
)
from .prompts import build_merge_conflict_prompt, build_watch_fix_prompt

logger = logging.getLogger(__name__)

POLL_INTERVAL = 180  # seconds


def _resolve_watch_target(
    args: argparse.Namespace, gl: gitlab.Gitlab, repo: Repo
) -> ProjectMergeRequest:
    """Resolve which MR to watch: explicit ref, or MR for the current branch."""
    if args.mr:
        try:
            ref = parse_mr_url_or_id(args.mr)
        except ValueError as e:
            logger.error("%s", e)
            sys.exit(1)
        return fetch_mr_by_ref(gl, repo, ref)
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)
    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)
    return mr


def _checkout_mr_branch(mr: ProjectMergeRequest, repo: Repo) -> str:
    """Check out the MR's source branch locally and return the branch name."""
    branch_name = mr.source_branch
    repo.git.fetch("origin")
    local_branches = [b.name for b in repo.branches]
    if branch_name in local_branches:
        repo.git.checkout(branch_name)
        repo.git.pull("origin", branch_name)
    else:
        repo.git.checkout("-b", branch_name, f"origin/{branch_name}")
    return branch_name


def _merge_main_into_branch(branch_name: str, repo: Repo) -> bool:
    """Fetch origin/main and merge it into the current branch.

    Returns True if merging was attempted (caller should skip further fixes and wait for
    the next pipeline). Returns False only if origin/main had no new commits.
    """
    repo.remotes.origin.fetch("main")

    ahead_commits = list(repo.iter_commits("HEAD..origin/main"))
    if not ahead_commits:
        return False

    print(f"  origin/main has {len(ahead_commits)} new commit(s) — merging...")
    head_before = repo.head.commit.hexsha
    clean_merge = False
    conflicting: list[str] = []
    try:
        repo.git.merge("origin/main", "--no-edit", "--no-verify")
        clean_merge = True
    except GitCommandError as e:
        logger.warning(
            "git merge failed (status %s):\nstdout: %s\nstderr: %s",
            e.status,
            e.stdout,
            e.stderr,
        )
        conflicting = repo.git.diff("--name-only", "--diff-filter=U").splitlines()
        print(
            f"  Merge conflict in {len(conflicting)} file(s): {', '.join(conflicting)}"
        )
        if not conflicting and repo.head.commit.hexsha == head_before:
            # Merge failed and HEAD didn't move — nothing to push, re-poll
            try:
                repo.git.merge("--abort")
            except GitCommandError:
                pass
            print("  Merge failed with no changes — re-polling.")
            return True
        if conflicting:
            with tempfile.TemporaryDirectory(
                prefix=".loom_merge_", dir=repo.working_dir
            ) as ctx:
                with open(
                    os.path.join(ctx, "conflicts.txt"), "w", encoding="utf-8"
                ) as f:
                    f.write("\n".join(conflicting))
                run_claude_agentic(
                    build_merge_conflict_prompt(branch_name, conflicting, ctx), repo
                )
            repo.git.add("-A")
            repo.git.commit(
                "--no-verify", "-m", f"chore: merge origin/main into {branch_name}"
            )

    repo.git.push("origin", branch_name)
    if clean_merge:
        print("  Merged origin/main cleanly and pushed.")
    elif conflicting:
        print("  Resolved merge conflicts and pushed.")
    else:
        print("  Merged origin/main (non-zero exit, no conflicts) and pushed.")
    return True


def _fix_failing_job_and_push(
    project: Project, pipeline: ProjectPipeline, branch_name: str, repo: Repo
) -> None:
    """Diagnose the first failing job via Claude and push any resulting commits."""
    job = fetch_first_failing_job(project, pipeline)
    if not job:
        print("Pipeline failed but no failing job found.")
        return

    print(f"\nFailing job: #{job.id} '{job.name}' (stage: {job.stage})")

    log = fetch_job_log(job)
    with tempfile.TemporaryDirectory(
        prefix=".loom_watch_", dir=repo.working_dir
    ) as ctx:
        with open(os.path.join(ctx, "job_log.txt"), "w", encoding="utf-8") as f:
            f.write(log)
        artifacts_dir = os.path.join(ctx, "artifacts")
        os.makedirs(artifacts_dir)
        extract_job_artifacts(job, artifacts_dir)
        run_claude_agentic(build_watch_fix_prompt(job, ctx, pipeline.id), repo)

    try:
        ahead = list(repo.iter_commits(f"origin/{branch_name}..HEAD"))
    except GitCommandError:
        ahead = []

    if ahead:
        repo.git.push("origin", branch_name)
        print(f"Pushed {len(ahead)} commit(s) to {branch_name}")
    else:
        print("No commits made.")


def _watch_approved_mrs(project: Project, repo: Repo) -> None:
    """Continuously watch all approved (or auto-merge) open MRs and fix failing
    pipelines."""
    print(
        "Watching approved, auto-merge, and active-pipeline MRs for pipeline failures...\n"
    )
    watched_iids: set[int] = set()

    try:
        while True:
            # Add newly qualifying MRs to the sticky set
            for mr in fetch_watched_mrs(project):
                watched_iids.add(mr.iid)

            # Re-fetch current state for all sticky MRs; drop closed/merged ones
            mrs: list[ProjectMergeRequest] = []
            stale: set[int] = set()
            for iid in watched_iids:
                mr = project.mergerequests.get(iid)
                if mr.state != "opened":
                    stale.add(iid)
                else:
                    mrs.append(mr)
            watched_iids -= stale

            if not mrs:
                print(
                    "No approved, auto-merge, or active-pipeline MRs found. Waiting..."
                )
                time.sleep(POLL_INTERVAL)
                continue

            print(f"Found {len(mrs)} MR(s) to watch:")
            for mr in mrs:
                print(f"  !{mr.iid}: {mr.title}")

            for mr in mrs:
                pipeline = fetch_latest_pipeline_for_mr(project, mr)
                if not pipeline:
                    continue
                print(f"\nMR !{mr.iid} pipeline #{pipeline.id}: {pipeline.status}")
                if pipeline.status != "failed":
                    continue

                print(f"  -> Fixing MR !{mr.iid}: {mr.title}")
                branch_name = _checkout_mr_branch(mr, repo)
                if _merge_main_into_branch(branch_name, repo):
                    continue
                _fix_failing_job_and_push(project, pipeline, branch_name, repo)

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped watching.")


def cmd_mr_watch(args: argparse.Namespace) -> None:
    """Watch an MR pipeline; auto-fix CI failures using Claude."""
    repo = Repo(os.getcwd())

    gl = _get_gitlab_client_or_exit()

    project = get_project(gl, repo)

    if args.all:
        _watch_approved_mrs(project, repo)
        return

    mr = _resolve_watch_target(args, gl, repo)
    branch_name = _checkout_mr_branch(mr, repo)

    print(f"\nWatching MR !{mr.iid}: {mr.title}")
    print(f"Branch: {branch_name}")
    print(f"URL: {mr.web_url}\n")

    try:
        while True:
            pipeline = fetch_latest_pipeline_for_mr(project, mr)

            if not pipeline:
                print("No pipeline yet, waiting...")
                time.sleep(POLL_INTERVAL)
                continue

            print(f"Pipeline #{pipeline.id}: {pipeline.status}  {pipeline.web_url}")

            if pipeline.status in PIPELINE_WAITING_STATUSES:
                time.sleep(POLL_INTERVAL)
                continue

            if pipeline.status == "success":
                print("Pipeline passed! ✓")
                _maybe_update_mr_description(mr, repo)
                break

            if pipeline.status != "failed":
                print(f"Pipeline ended with status '{pipeline.status}' — stopping.")
                break

            if _merge_main_into_branch(branch_name, repo):
                time.sleep(POLL_INTERVAL)
                continue
            _fix_failing_job_and_push(project, pipeline, branch_name, repo)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped watching.")
