import argparse
import logging
import os
import sys

from git import Repo
from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Project

from ._common import _ask, _get_gitlab_client_or_exit
from .claude import generate_release_notes_via_claude, is_claude_cli_installed
from .git_helpers import fetch_and_sort_tags, get_tag_diff
from .gitlab_api import (
    fetch_milestone_for_tag,
    find_previous_tag,
    format_milestone_items,
    get_project,
    prompt_tag_selection,
)

logger = logging.getLogger(__name__)


def _check_existing_release(project: Project, tag_name: str) -> bool:
    """Check if a release already exists and confirm overwrite if so.

    Returns True if the caller should proceed, False if aborted.
    """
    try:
        existing = project.releases.get(tag_name)
    except GitlabGetError:
        return True  # Release doesn't exist yet — proceed normally
    print(f"\nRelease {tag_name!r} already exists: {existing.name}")
    answer = _ask("Overwrite existing release? [y/N]: ")
    if answer != "y":
        print("Aborted.")
        return False
    return True


def _get_milestone_context(project: Project, tag_name: str) -> str:
    """Look up the milestone matching tag_name and return formatted MR/issue info."""
    logger.info("Looking up milestone for tag %s...", tag_name)
    milestone = fetch_milestone_for_tag(project, tag_name)
    if not milestone:
        logger.info("No milestone found matching tag %s", tag_name)
        return ""
    logger.info("Found milestone: %s", milestone.title)
    mrs = project.mergerequests.list(
        milestone=milestone.title, state="merged", all=True
    )
    issues = project.issues.list(milestone=milestone.title, all=True)
    logger.info("Milestone contains %d MR(s) and %d issue(s)", len(mrs), len(issues))
    return format_milestone_items(mrs, issues)


def cmd_release(_args: argparse.Namespace) -> None:
    """Create a GitLab release with AI-generated release notes."""
    repo = Repo(os.getcwd())

    gl = _get_gitlab_client_or_exit()

    project = get_project(gl, repo)

    logger.info("Fetching tags...")
    tags = fetch_and_sort_tags(repo)
    if not tags:
        logger.error("No tags found in this repository.")
        sys.exit(1)

    tag_name = prompt_tag_selection(tags)
    previous_tag = find_previous_tag(tags, tag_name)
    logger.info("Selected tag: %s (previous: %s)", tag_name, previous_tag or "none")

    if not _check_existing_release(project, tag_name):
        return

    milestone_info = _get_milestone_context(project, tag_name)

    diff = (
        get_tag_diff(repo, previous_tag, tag_name)
        if previous_tag
        else "(No previous tag — this appears to be the first release.)"
    )

    if not is_claude_cli_installed():
        logger.error("Claude CLI not installed.")
        sys.exit(1)

    release_notes = generate_release_notes_via_claude(
        tag_name, previous_tag, milestone_info, diff, repo
    )
    if not release_notes:
        logger.error("Failed to generate release notes via Claude.")
        sys.exit(1)

    print("\n--- Release Notes Preview ---")
    print(f"Tag: {tag_name}\n")
    print(release_notes)
    print("--- End Preview ---\n")

    answer = _ask(
        f"Create GitLab release for {tag_name!r} with the above notes? [Y/n]: "
    )
    if answer not in ("", "y"):
        print("Aborted.")
        return

    project.releases.create(
        {
            "name": tag_name,
            "tag_name": tag_name,
            "description": release_notes,
        }
    )
    logger.info("Created release %s", tag_name)
    print(f"Release {tag_name!r} created successfully.")
