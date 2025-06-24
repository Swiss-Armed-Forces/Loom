#!/usr/bin/env python3
import argparse
import gzip
import logging
import os
import re
import shlex
import subprocess
from pathlib import Path

import docker
from docker.errors import ImageNotFound, ImageLoadError

# -------------------------------
# Constants
# -------------------------------
DOCKER_CLIENT_TIMEOUT = 600  # 10 minutes

# -------------------------------
# Logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# -------------------------------
# Minikube Env Loader
# -------------------------------
def load_minikube_env():
    """
    Runs `minikube -p minikube docker-env`, parses its export statements,
    and sets them in os.environ.
    """
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
        key, val = line[len("export ") :].split("=", 1)
        val = shlex.split(val)[0]  # Remove surrounding quotes
        os.environ[key] = val
        logger.debug("Set env %s=%s", key, val)
    logger.info("Successfully loaded Minikube Docker environment.")


# -------------------------------
# Utility Functions
# -------------------------------
def format_file_size(file_path: Path) -> str:
    if not file_path.exists():
        return "File not found"
    size_bytes = file_path.stat().st_size
    for divisor, unit in [
        (1024**4, "TiB"),
        (1024**3, "GiB"),
        (1024**2, "MiB"),
        (1024**1, "KiB"),
        (1, "bytes"),
    ]:
        if size_bytes >= divisor:
            size = size_bytes / divisor
            return f"{size:.2f} {unit}" if unit != "bytes" else f"{int(size)} {unit}"
    return "0 bytes"


def get_docker_client() -> docker.DockerClient:
    return docker.from_env(timeout=DOCKER_CLIENT_TIMEOUT)


def get_matching_images(pattern: str) -> list[str]:
    client = get_docker_client()
    regex = re.compile(pattern)
    names = []
    for image in client.images.list():
        for tag in image.tags:
            if regex.fullmatch(tag):
                names.append(tag)
    return names


def get_matching_archive_files(directory: Path, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    matches = []
    for f in directory.glob("*.tar.gz"):
        name = f.name.removesuffix(".tar.gz").replace("_", "/")  # reverse normalization
        if regex.fullmatch(name):
            matches.append(name)
    return matches


# -------------------------------
# Image Backup & Restore
# -------------------------------
def docker_backup_image(image_name: str, backup_dir: Path):
    """
    Backup a Docker image to a compressed .tar.gz archive.

    Uses a temporary `.progress` file during write to avoid partial results.
    """
    client = get_docker_client()
    backup_dir.mkdir(parents=True, exist_ok=True)

    archive_name = image_name.replace("/", "_") + ".tar.gz"
    archive_path = backup_dir / archive_name
    temp_path = archive_path.with_suffix(".tar.gz.progress")

    if archive_path.exists():
        logger.info("Archive already exists for image '%s'. Skipping.", image_name)
        return

    try:
        image = client.images.get(image_name)
    except ImageNotFound:
        logger.warning("Image '%s' not found. Skipping.", image_name)
        return

    logger.info("Backing up image '%s' to '%s'...", image_name, archive_path)

    try:
        with gzip.open(temp_path, "wb") as f:
            for chunk in image.save(named=True):
                f.write(chunk)
        temp_path.replace(archive_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    logger.info(
        "Backup complete for image '%s' (%s).",
        image_name,
        format_file_size(archive_path),
    )


def docker_restore_image(image_name: str, backup_dir: Path) -> None:
    """
    Restore a Docker image from a compressed .tar.gz archive if it is not already loaded.
    """
    archive_path = backup_dir / (image_name.replace("/", "_") + ".tar.gz")
    if not archive_path.exists():
        logger.warning("Archive for image '%s' not found. Skipping.", image_name)
        return

    client = get_docker_client()

    try:
        client.images.get(image_name)
        logger.info("Image '%s' already exists. Skipping restore.", image_name)
        return
    except ImageNotFound:
        pass  # Continue to restore

    logger.info("Restoring image '%s' from '%s'...", image_name, archive_path)

    try:
        with open(archive_path, "rb") as f:
            client.images.load(f)  # type: ignore
    except ImageLoadError as e:
        logger.warning("Failed to load image '%s': %s. Skipping.", image_name, e)
        return

    logger.info(
        "Restore complete for image '%s' (%s).",
        image_name,
        format_file_size(archive_path),
    )


# -------------------------------
# CLI Entry Point
# -------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Backup and restore Docker images.")
    parser.add_argument(
        "-m", "--minikube", action="store_true", help="Load Minikube Docker env."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_bi = subparsers.add_parser("backup", help="Backup Docker images by regex.")
    parser_bi.add_argument("pattern", help="Regex pattern to match image names.")
    parser_bi.add_argument("directory", type=Path, help="Backup destination directory.")

    parser_ri = subparsers.add_parser("restore", help="Restore Docker images by regex.")
    parser_ri.add_argument("pattern", help="Regex pattern to match archive names.")
    parser_ri.add_argument("directory", type=Path, help="Backup source directory.")

    args = parser.parse_args()

    if args.minikube:
        load_minikube_env()

    match args.command:
        case "backup":
            for name in get_matching_images(args.pattern):
                docker_backup_image(name, args.directory)
        case "restore":
            for name in get_matching_archive_files(args.directory, args.pattern):
                docker_restore_image(name, args.directory)


if __name__ == "__main__":
    main()
