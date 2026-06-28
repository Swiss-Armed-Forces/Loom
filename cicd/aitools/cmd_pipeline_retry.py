import argparse
import logging
import os
import sys

from git import Repo

from ._common import _get_gitlab_client_or_exit
from .config import CI_PROJECT_ID
from .gitlab_api import (
    get_project_id_from_remote,
    parse_pipeline_url_or_id,
    retry_pipeline,
)

logger = logging.getLogger(__name__)


def cmd_pipeline_retry(args: argparse.Namespace) -> None:
    """Retry a GitLab pipeline by ID or URL."""
    repo = Repo(os.getcwd())

    try:
        ref = parse_pipeline_url_or_id(args.pipeline)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    gl = _get_gitlab_client_or_exit()

    project_path = ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error(
            "Could not determine project. Provide a full pipeline URL or set CI_PROJECT_ID."
        )
        sys.exit(1)

    project = gl.projects.get(project_path)
    retry_pipeline(project, ref.pipeline_id)
    print(f"Retried pipeline #{ref.pipeline_id}")
