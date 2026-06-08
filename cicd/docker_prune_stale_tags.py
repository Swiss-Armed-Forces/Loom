#!/usr/bin/env python3
import argparse
import logging
import os
import shlex
import subprocess
from collections import defaultdict

import docker

# -------------------------------
# Constants
# -------------------------------
DOCKER_CLIENT_TIMEOUT = 20 * 60
LATEST_TAG_NAME = "latest"
LOG_LEVEL = logging.INFO

# -------------------------------
# Logging Setup
# -------------------------------
logger = logging.getLogger()


# -------------------------------
# Minikube Env Loader
# -------------------------------
def load_minikube_env() -> None:
    proc = subprocess.run(
        ["minikube", "-p", "minikube", "docker-env"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        key, val = line[len("export "):].split("=", 1)
        val = shlex.split(val)[0]
        os.environ[key] = val
    logger.info("Successfully loaded Minikube Docker environment.")


# -------------------------------
# Core Logic
# -------------------------------
def prune_stale_tags(dry_run: bool) -> None:
    client = docker.from_env(timeout=DOCKER_CLIENT_TIMEOUT)

    # Group tags by repository -> image ID
    repo_id_tags: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for image in client.images.list():
        for full_tag in image.tags:
            repo, _, tag = full_tag.rpartition(":")
            repo_id_tags[repo][image.short_id].append(tag)

    tags_to_remove: list[str] = []

    for repo, id_tags in repo_id_tags.items():
        # Find the image ID that the latest tag points to
        latest_id = next(
            (img_id for img_id, tags in id_tags.items() if LATEST_TAG_NAME in tags),
            None,
        )
        if latest_id is None:
            continue

        for img_id, tags in id_tags.items():
            if img_id == latest_id:
                continue
            # This image ID differs from latest — remove all its tags
            for tag in tags:
                tags_to_remove.append(f"{repo}:{tag}")

    if not tags_to_remove:
        logger.info("No stale tags found.")
        return

    logger.info("Found %d stale tag(s) to remove.", len(tags_to_remove))
    for full_tag in sorted(tags_to_remove):
        if dry_run:
            logger.info("[dry-run] Would remove: %s", full_tag)
        else:
            logger.info("Removing: %s", full_tag)
            client.images.remove(full_tag, force=False, noprune=True)

    if not dry_run:
        logger.info("Done. Removed %d stale tag(s).", len(tags_to_remove))


# -------------------------------
# CLI Entry Point
# -------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Remove Docker image tags that point to a different image than the "
            "'latest' tag of the same repository."
        )
    )
    parser.add_argument(
        "-m", "--minikube", action="store_true", help="Use Minikube's Docker daemon."
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Print what would be removed without removing."
    )
    args = parser.parse_args()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(console_handler)
    logger.setLevel(LOG_LEVEL)

    if args.minikube:
        load_minikube_env()

    prune_stale_tags(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
