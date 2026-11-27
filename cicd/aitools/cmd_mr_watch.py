import argparse
import logging
import os
import time

from git import Repo
from gitlab.exceptions import GitlabError
from gitlab.v4.objects import Project, ProjectMergeRequest

from ._common import (
    _get_gitlab_client_or_exit,
    _maybe_update_mr_description,
    acquire_mr_worktree,
    fix_failing_job_and_push,
    resolve_mr_from_args_or_branch,
)
from .gitlab_api import (
    PIPELINE_WAITING_STATUSES,
    fetch_latest_pipeline_for_mr,
    fetch_watched_mrs,
    get_project,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL = 180  # seconds


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

                # Acquired only now: an MR that is merely being observed should not
                # grow a worktree, let alone a devenv environment inside it.
                print(f"  -> Fixing MR !{mr.iid}: {mr.title}")
                worktree = acquire_mr_worktree(mr, repo)
                fix_failing_job_and_push(project, pipeline, worktree)

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped watching.")


def cmd_mr_watch(args: argparse.Namespace) -> None:
    """Watch an MR pipeline; auto-fix CI failures using AI."""
    repo = Repo(os.getcwd())

    gl = _get_gitlab_client_or_exit()

    project = get_project(gl, repo)

    if args.all:
        _watch_approved_mrs(project, repo)
        return

    mr = resolve_mr_from_args_or_branch(gl, args, repo)
    worktree = acquire_mr_worktree(mr, repo)

    print(f"\nWatching MR !{mr.iid}: {mr.title}")
    print(f"Branch: {worktree.branch}")
    print(f"Worktree: {worktree.path}")
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
                _maybe_update_mr_description(mr, worktree.repo)
                break

            if pipeline.status != "failed":
                print(f"Pipeline ended with status '{pipeline.status}' — stopping.")
                break

            fix_failing_job_and_push(project, pipeline, worktree)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped watching.")
