import argparse
import logging
import os
import tempfile
import time

from git import Repo
from git.exc import GitCommandError
from gitlab.exceptions import GitlabError
from gitlab.v4.objects import Project, ProjectMergeRequest, ProjectPipeline

from ._common import (
    _get_gitlab_client_or_exit,
    _maybe_update_mr_description,
    checkout_mr_branch,
    resolve_mr_from_args_or_branch,
)
from .claude import run_claude_agentic
from .gitlab_api import (
    PIPELINE_WAITING_STATUSES,
    extract_job_artifacts,
    fetch_first_failing_job,
    fetch_job_log,
    fetch_latest_pipeline_for_mr,
    fetch_watched_mrs,
    get_project,
)
from .prompts import build_watch_fix_prompt

logger = logging.getLogger(__name__)

POLL_INTERVAL = 180  # seconds


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
                try:
                    mr = project.mergerequests.get(iid)
                except GitlabError as e:
                    logger.warning(
                        "Failed to fetch MR !%s, dropping from watch: %s", iid, e
                    )
                    stale.add(iid)
                    continue
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
                branch_name = checkout_mr_branch(mr, repo)
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

    mr = resolve_mr_from_args_or_branch(gl, args, repo)
    branch_name = checkout_mr_branch(mr, repo)

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

            _fix_failing_job_and_push(project, pipeline, branch_name, repo)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped watching.")
