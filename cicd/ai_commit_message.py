#!/usr/bin/env python3

import logging
import os
import shutil
import subprocess
import sys

from git import Repo

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "30"))


def get_staged_diff(repo: Repo) -> str:
    """Return the staged diff for the current repository."""
    diff = repo.git.diff("--cached")
    logger.debug("Staged diff retrieved: %s", diff)
    return diff


def is_claude_cli_installed() -> bool:
    """Check if the Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def generate_commit_message(diff: str, repo: Repo) -> str | None:
    """Generate a commit message using the Claude Code CLI."""
    prompt = f"""Generate a git commit message for the following diff.

Format:
- First line: conventional commit format (type(scope): description), max 72 characters
- Blank line
- A brief paragraph summarizing the changes
- Sections like "Added:", "Changed:", "Removed:", "Fixed:" followed by bullet points (use "- " for bullets)

Rules:
- Describe what changed, not why
- Output only the raw commit message text, nothing else
- Do NOT use markdown formatting (no code blocks, no # headers)
- Lines starting with # are git comments and will be ignored

Diff:
{diff}
"""

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
                prompt,
            ],
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


def update_commit_msg_file(file_path: str, message: str) -> None:
    """Overwrite the commit message file with the AI-generated message."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(message + "\n")
    logger.info("Commit message file updated.")


def is_standard_commit_msg_file(filepath: str) -> bool:
    """Check if the commit message file is for a normal new commit."""
    return os.path.basename(filepath) == "COMMIT_EDITMSG"


def main():
    logger.debug("Called with arguments: %s", sys.argv)

    if len(sys.argv) < 2:
        logger.error(
            "This script must be run as a prepare-commit-msg hook with the commit message file path."
        )
        sys.exit(1)

    # Check if Claude CLI is installed
    if not is_claude_cli_installed():
        logger.debug("Claude CLI not installed, skipping AI commit message generation.")
        return

    commit_msg_filepath = sys.argv[1]
    logger.info("Preparing commit message using file: %s", commit_msg_filepath)

    # Only generate commit message for new, standard commits
    if not is_standard_commit_msg_file(commit_msg_filepath):
        logger.info(
            "Non-standard commit message context detected, skipping AI generation."
        )
        return

    repo = Repo(os.getcwd())

    diff = get_staged_diff(repo)
    if not diff:
        logger.info("No staged changes found, skipping AI commit message generation.")
        return

    message = generate_commit_message(diff, repo)

    if message:
        update_commit_msg_file(commit_msg_filepath, message)
    else:
        logger.warning("No suggested message available; leaving existing message.")


if __name__ == "__main__":
    main()
