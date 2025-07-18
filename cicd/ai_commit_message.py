#!/usr/bin/env python3

import os
import sys
import logging

from git import Repo
from httpx import HTTPError
from ollama import Client, Options, RequestError, ResponseError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mevatron/diffsense:1.5b")
OLLAMA_CLIENT_TIMEOUT = int(os.getenv("OLLAMA_CLIENT_TIMEOUT", "60"))
OLLAMA_CONNECTION_TEST_CLIENT_TIMEOUT = int(
    os.getenv("OLLAMA_CONNECTION_TEST_CLIENT_TIMEOUT", "1")
)
OLLAMA_PULL_CLIENT_TIMEOUT = int(os.getenv("OLLAMA_PULL_CLIENT_TIMEOUT", "180"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama.loom")
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "1024"))
OLLAMA_SYSTEM_PROMPT = (
    "You are a helpful assistant that writes conventional git commit messages. "
    "Given a git diff, generate a clear, concise commit message summarizing the changes. "
    "Just describe the change, do not explain why this change is required. "
    f"Output only the commit message in {OLLAMA_MAX_TOKENS} tokens or less."
)

# Initialize Ollama client
ollama_client = Client(host=f"http://{OLLAMA_HOST}", timeout=OLLAMA_CLIENT_TIMEOUT)
ollama_connection_test_client = Client(
    host=f"http://{OLLAMA_HOST}", timeout=OLLAMA_CONNECTION_TEST_CLIENT_TIMEOUT
)
ollama_pull_client = Client(
    host=f"http://{OLLAMA_HOST}", timeout=OLLAMA_PULL_CLIENT_TIMEOUT
)


def get_staged_diff(repo: Repo) -> str:
    """Return the staged diff for the current repository."""
    diff = repo.git.diff("--cached")
    logger.debug("Staged diff retrieved: %s", diff)
    return diff


def generate_commit_message(diff: str) -> str | None:
    """Generate a commit message using the Ollama client."""
    try:
        logger.info("Testing connection to: %s", OLLAMA_HOST)
        ollama_connection_test_client.ps()
        logger.info("Pulling ollama model: %s", OLLAMA_MODEL)
        ollama_pull_client.pull(model=OLLAMA_MODEL)
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
    except (
        HTTPError,
        ConnectionError,
        RequestError,
        ResponseError,
    ) as e:
        logger.warning("Ollama error (%s): %s", OLLAMA_HOST, e)
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
    message = generate_commit_message(diff)

    if message:
        update_commit_msg_file(commit_msg_filepath, message)
    else:
        logger.warning("No suggested message available; leaving existing message.")


if __name__ == "__main__":
    main()
