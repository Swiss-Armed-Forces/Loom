#!/usr/bin/env python3

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys

import gitlab
import requests
from git import Repo
from gitlab.v4.objects import ProjectMergeRequest

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants from environment variables
CI_SERVER_HOST = os.getenv("CI_SERVER_HOST", "gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN") or os.getenv("PROJECT_ACCESS_TOKEN")
CI_PROJECT_ID = os.getenv("CI_PROJECT_ID")
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "120"))


def get_branch_diff(repo: Repo) -> str:
    """Return the diff between current branch and origin/main."""
    repo.git.fetch("origin", "main")
    diff = repo.git.diff("origin/main...HEAD")
    logger.debug("Branch diff retrieved: %d characters", len(diff) if diff else 0)
    return diff


def load_mr_template(repo: Repo) -> str:
    """Load the MR template from the repository."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return ""

    template_path = os.path.join(
        repo.working_dir, ".gitlab", "merge_request_templates", "Default.md"
    )
    try:
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("MR template not found at %s", template_path)
        return ""


def build_prompt(
    mr_template: str,
    current_title: str = "",
    current_description: str = "",
    include_diff: str | None = None,
    user_instructions: str = "",
) -> str:
    """Build the prompt for commit message generation.

    Args:
        mr_template: The MR template content to include in instructions.
        current_title: The current MR title (as a hint for the AI).
        current_description: The current MR description (as a hint for the AI).
        include_diff: If provided, append the diff to the prompt (for Claude CLI).
                      If None, diff should be passed separately (for GitLab Duo).
        user_instructions: Additional user instructions to append to the prompt.
    """
    template_instruction = ""
    if mr_template:
        template_instruction = f"""
- MR description body should follow this template:

{mr_template}

For the Summary section, write a brief paragraph summarizing the changes, followed by
sections like "Added:", "Changed:", "Removed:", "Fixed:" with bullet points (use "- " for bullets).

Leave the Issue Reference section empty (it will be filled manually).
"""

    current_mr_hint = ""
    if current_title or current_description:
        current_mr_hint = "\nCurrent MR content (use as reference):\n"
        if current_title:
            current_mr_hint += f"Title: {current_title}\n"
        if current_description:
            current_mr_hint += f"Description:\n{current_description}\n"

    prompt = f"""Generate a git commit message and MR description for the following diff.

Format:
- First line: conventional commit format (type(scope): description), max 72 characters
- Blank line
{template_instruction}
Rules:
- Describe what changed, not why
- Output only the raw commit message text, nothing else
- Do NOT wrap output in code fences or markdown code blocks
- Use markdown formatting for the body (headers with #, bullet points with -)
- Preserve external references from the current description if still relevant (e.g., "Closes #123",
  "Related to #456", links to issues/MRs, or other cross-references)
{current_mr_hint}"""

    if user_instructions:
        prompt += f"\nAdditional user instructions:\n{user_instructions}\n"

    if include_diff:
        prompt += f"\nDiff:\n{include_diff}\n"

    return prompt


def generate_commit_message_via_duo(
    diff: str,
    mr_template: str,
    current_title: str = "",
    current_description: str = "",
    user_instructions: str = "",
) -> str | None:
    """Generate a commit message using GitLab Duo Chat API."""
    if not GITLAB_TOKEN:
        logger.warning("No GitLab token available for Duo API")
        return None

    prompt = build_prompt(
        mr_template, current_title, current_description, user_instructions=user_instructions
    )

    url = f"https://{CI_SERVER_HOST}/api/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {GITLAB_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "content": prompt,
        "additional_context": [
            {
                "category": "file",
                "id": "changes.diff",
                "content": diff,
            }
        ],
    }

    try:
        logger.info("Sending diff to GitLab Duo for commit message suggestion...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        message = response.json().get("content", "").strip()
        logger.debug("GitLab Duo response: %s", message)
        return message if message else None
    except requests.RequestException as e:
        logger.warning("GitLab Duo API request failed: %s", e)
        return None


def is_claude_cli_installed() -> bool:
    """Check if the Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def generate_commit_message_via_claude(
    diff: str,
    mr_template: str,
    repo: Repo,
    current_title: str = "",
    current_description: str = "",
    user_instructions: str = "",
) -> str | None:
    """Generate a commit message using the Claude Code CLI."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return None

    prompt = build_prompt(
        mr_template,
        current_title,
        current_description,
        include_diff=diff,
        user_instructions=user_instructions,
    )

    try:
        logger.info("Sending diff to Claude CLI for commit message suggestion...")
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--output-format",
                "text",
                "--max-turns",
                "1",
                "--no-session-persistence",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=repo.working_dir,
            check=False,
        )

        if result.returncode != 0:
            logger.warning("Claude CLI returned non-zero exit code: %s", result.returncode)
            if result.stderr:
                logger.warning("Claude CLI stderr: %s", result.stderr)
            return None

        message = result.stdout.strip()
        logger.debug("Claude CLI response: %s", message)
        return message if message else None

    except subprocess.TimeoutExpired:
        logger.warning("Claude CLI timed out after %s seconds", CLAUDE_TIMEOUT)
        return None
    except OSError as e:
        logger.warning("Failed to run Claude CLI: %s", e)
        return None


def parse_commit_message(message: str) -> tuple[str, str]:
    """Split commit message into title (first line) and body (rest)."""
    lines = message.strip().split("\n", 1)
    title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    return title, body


def get_gitlab_client() -> gitlab.Gitlab | None:
    """Create GitLab client from environment variables."""
    if not GITLAB_TOKEN:
        logger.warning("No GitLab token found (GITLAB_TOKEN or PROJECT_ACCESS_TOKEN)")
        return None
    return gitlab.Gitlab(f"https://{CI_SERVER_HOST}", private_token=GITLAB_TOKEN)


def get_project_id_from_remote(repo: Repo) -> str | None:
    """Try to infer GitLab project path from git remote URL."""
    try:
        remote_url = repo.remotes.origin.url
        # Handle SSH URLs: git@gitlab.com:group/project.git
        ssh_match = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", remote_url)
        if ssh_match:
            return ssh_match.group(1)
        # Handle HTTPS URLs: https://gitlab.com/group/project.git
        https_match = re.match(r"https?://[^/]+/(.+?)(?:\.git)?$", remote_url)
        if https_match:
            return https_match.group(1)
    except Exception as e:
        logger.debug("Failed to parse remote URL: %s", e)
    return None


def find_open_mr_for_branch(
    gl: gitlab.Gitlab, branch: str, repo: Repo
) -> ProjectMergeRequest | None:
    """Find an open MR for the given source branch."""
    project_id = CI_PROJECT_ID
    if not project_id:
        # Try to infer from git remote
        project_id = get_project_id_from_remote(repo)
        if not project_id:
            logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
            return None

    logger.info("Using project ID: %s", project_id)
    project = gl.projects.get(project_id)
    mrs = project.mergerequests.list(source_branch=branch, state="opened", per_page=1)
    return mrs[0] if mrs else None


def update_mr(mr: ProjectMergeRequest, title: str, description: str) -> None:
    """Update MR title and description."""
    mr.title = title
    mr.description = description
    mr.save()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update MR title and description using AI-generated content."
    )
    parser.add_argument(
        "instructions",
        nargs="*",
        help="Additional instructions to append to the AI prompt",
    )
    args = parser.parse_args()
    user_instructions = " ".join(args.instructions) if args.instructions else ""

    if user_instructions:
        logger.info("User instructions: %s", user_instructions)

    repo = Repo(os.getcwd())
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)

    # Connect to GitLab and find MR first
    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)

    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)

    logger.info("Found MR !%s: %s", mr.iid, mr.title)

    # Get current MR title and description as hints for the AI
    current_title = mr.title or ""
    current_description = mr.description or ""

    # Get diff against origin/main
    diff = get_branch_diff(repo)
    if not diff:
        logger.info("No changes compared to origin/main.")
        return

    # Load MR template and generate commit message
    mr_template = load_mr_template(repo)

    # Try GitLab Duo first, fall back to Claude CLI
    message = generate_commit_message_via_duo(
        diff, mr_template, current_title, current_description, user_instructions
    )
    if not message:
        logger.info("GitLab Duo unavailable, trying Claude CLI fallback...")
        if not is_claude_cli_installed():
            logger.error("Claude CLI not installed and GitLab Duo unavailable.")
            sys.exit(1)
        message = generate_commit_message_via_claude(
            diff, mr_template, repo, current_title, current_description, user_instructions
        )
        if not message:
            logger.error("Failed to generate commit message via both methods.")
            sys.exit(1)

    title, body = parse_commit_message(message)
    logger.info("Generated title: %s", title)
    logger.info("Generated body:\n%s", body)

    # Update MR
    update_mr(mr, title, body)
    logger.info("Updated MR !%s", mr.iid)


if __name__ == "__main__":
    main()
