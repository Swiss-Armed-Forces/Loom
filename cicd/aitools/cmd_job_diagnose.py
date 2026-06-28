import argparse
import logging
import os
import sys
import tempfile

from git import Repo

from ._common import _get_gitlab_client_or_exit
from .claude import run_claude_agentic
from .config import CI_PROJECT_ID
from .gitlab_api import (
    extract_job_artifacts,
    fetch_job_log,
    get_project_id_from_remote,
    parse_job_url_or_id,
)
from .prompts import build_diagnose_prompt

logger = logging.getLogger(__name__)


def cmd_job_diagnose(args: argparse.Namespace) -> None:
    """Diagnose a CI/CD job failure using Claude in agentic mode."""
    repo = Repo(os.getcwd())

    try:
        job_ref = parse_job_url_or_id(args.job)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    gl = _get_gitlab_client_or_exit()

    project_path = (
        job_ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    )
    if not project_path:
        logger.error(
            "Could not determine project. Provide a full job URL or set CI_PROJECT_ID."
        )
        sys.exit(1)

    logger.info("Using project: %s", project_path)
    project = gl.projects.get(project_path)
    job = project.jobs.get(job_ref.job_id)

    print(f"\nJob #{job.id}: {job.name}")
    print(f"Stage: {job.stage} | Status: {job.status}")
    print(f"URL: {job.web_url}\n")

    logger.info("Fetching job log...")
    log = fetch_job_log(job)
    logger.info("Job log: %d characters", len(log))

    with tempfile.TemporaryDirectory(
        prefix=".loom_diagnose_", dir=repo.working_dir
    ) as context_dir:
        with open(os.path.join(context_dir, "job_log.txt"), "w", encoding="utf-8") as f:
            f.write(log)

        logger.info("Fetching job artifacts...")
        artifacts_dir = os.path.join(context_dir, "artifacts")
        os.makedirs(artifacts_dir)
        if extract_job_artifacts(job, artifacts_dir):
            logger.info("Artifacts extracted to %s", artifacts_dir)
        else:
            logger.info("No artifacts found")

        prompt = build_diagnose_prompt(job, context_dir, job.pipeline["id"])
        run_claude_agentic(prompt, repo)
