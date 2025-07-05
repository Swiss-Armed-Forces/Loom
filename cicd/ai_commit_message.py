#!/usr/bin/env python3

import os
import sys
import logging

from git import Repo
from ollama import Client, Options, RequestError, ResponseError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mevatron/diffsense:1.5b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama.loom")
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "1024"))
OLLAMA_SYSTEM_PROMPT = (
    "You are a helpful assistant that writes conventional git commit messages. "
    "Given a git diff, generate a clear, concise commit message summarizing the changes. "
    "Just describe the change, do not explain why this change is required. "
    f"Output only the commit message in {OLLAMA_MAX_TOKENS} tokens or less."
)

# Initialize Ollama client
ollama_client = Client(host=f"http://{OLLAMA_HOST}")


def get_staged_diff(repo: Repo) -> str:
    """Return the staged diff for the current repository."""
    diff = repo.git.diff("--cached")
    logger.debug("Staged diff retrieved: %s", diff)
    return diff


def generate_commit_message(diff: str) -> str | None:
    """Generate a commit message using the Ollama client."""
    try:
        logger.info("Pulling ollama model: %s", OLLAMA_MODEL)
        ollama_client.pull(model=OLLAMA_MODEL)
        logger.info("Sending diff to Ollama for commit message suggestion...")

        response = ollama_client.generate(
            model=OLLAMA_MODEL,
            prompt=diff,
            system=OLLAMA_SYSTEM_PROMPT,
            options=Options(
                num_predict=OLLAMA_MAX_TOKENS,
            ),
        )
        logger.debug("Ollama response: %s", response)
        return response.response
    except (ConnectionError, RequestError, ResponseError) as e:
        logger.warning("Ollama error (%s): %s", OLLAMA_HOST, e)
        return None


def update_commit_msg_file(file_path: str, message: str) -> None:
    """Overwrite the commit message file with the AI-generated message."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(message + "\n")
    logger.info("Commit message file updated.")


def is_merge_commit_from_hook_args() -> bool:
    """Determine if this is a merge commit based on hook arguments."""
    # Check if the commit message file is MERGE_MSG (indicates merge)
    if len(sys.argv) >= 2:
        commit_msg_file = sys.argv[1]
        return commit_msg_file.endswith("MERGE_MSG")

    # Alternative: check if third argument is "merge" (for other cases)
    return len(sys.argv) >= 3 and sys.argv[2] == "merge"


def main():
    logger.debug("Called with arguments: %s", sys.argv)

    if len(sys.argv) < 2:
        logger.error(
            "This script must be run as a prepare-commit-msg hook with the commit message file path."
        )
        sys.exit(1)

    commit_msg_filepath = sys.argv[1]
    logger.info("Preparing commit message using file: %s", commit_msg_filepath)

    repo = Repo(os.getcwd())

    if is_merge_commit_from_hook_args():
        logger.info("Merge commit detected, skipping AI generation.")
        return

    diff = get_staged_diff(repo)
    message = generate_commit_message(diff)

    if message:
        update_commit_msg_file(commit_msg_filepath, message)
    else:
        logger.warning("No suggested message available; leaving existing message.")


if __name__ == "__main__":
    main()
