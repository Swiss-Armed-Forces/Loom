#!/usr/bin/env python3
import argparse
import logging
import os
import re
import shlex
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from multiprocessing.queues import Queue as MPQueue
from pathlib import Path

import docker
import zstandard as zstd
from docker.errors import ImageLoadError, ImageNotFound
from pydantic import BaseModel

# -------------------------------
# Constants
# -------------------------------
DOCKER_CLIENT_TIMEOUT = 20 * 60
DOCKER_SAVE_CHUNK_SIZE = 100 * 1024**2
ZSTD_COMPRESSION_LEVEL = 3
LOG_LEVEL = logging.INFO

# -------------------------------
# Logging Setup
# -------------------------------
log_queue: MPQueue = Queue()
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
)
listener = QueueListener(log_queue, console_handler)


# -------------------------------
# Models
# -------------------------------
class ImageMetadata(BaseModel):
    id: str
    tags: list[str]


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
        key, val = line[len("export ") :].split("=", 1)
        val = shlex.split(val)[0]  # Remove surrounding quotes
        os.environ[key] = val
        logger.debug("Set env %s=%s", key, val)
    logger.info("Successfully loaded Minikube Docker environment.")


# -------------------------------
# Utilities
# -------------------------------
def format_size(size_bytes: int) -> str:
    for divisor, unit in [
        (1024**4, "TiB"),
        (1024**3, "GiB"),
        (1024**2, "MiB"),
        (1024, "KiB"),
        (1, "bytes"),
    ]:
        if size_bytes >= divisor:
            size = size_bytes / divisor
            return f"{size:.2f} {unit}" if unit != "bytes" else f"{int(size)} {unit}"
    return "0 bytes"


def format_file_path_size(file_path: Path) -> str:
    if not file_path.exists():
        return "File not found"
    size_bytes = file_path.stat().st_size
    return format_size(size_bytes)


def get_docker_client() -> docker.DockerClient:
    return docker.from_env(timeout=DOCKER_CLIENT_TIMEOUT)


def get_image_map(pattern: str) -> list[ImageMetadata]:
    client = get_docker_client()
    regex = re.compile(pattern)
    images = []
    for image in client.images.list():
        if not image.id:
            logger.warning("Skipping image with no ID.")
            continue
        matching_tags = [tag for tag in image.tags if regex.fullmatch(tag)]
        if matching_tags:
            images.append(ImageMetadata(id=image.id, tags=matching_tags))
    return images


# -------------------------------
# Logging in Subprocesses
# -------------------------------
def setup_subprocess_logging() -> None:
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(QueueHandler(log_queue))
    logging.getLogger().setLevel(LOG_LEVEL)


# -------------------------------
# Docker Backup & Restore
# -------------------------------
def docker_backup_image(meta: ImageMetadata, backup_dir: Path) -> None:
    setup_subprocess_logging()
    client = get_docker_client()

    image_dir = backup_dir / meta.id
    archive_path = image_dir / "image.tar.zst"
    temp_path = image_dir / "image.tar.zst.progress"
    metadata_path = image_dir / "meta.json"

    # Create the backup directory if it doesn't exist
    logger.info("Creating: %s", image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    if not archive_path.exists():
        try:
            image = client.images.get(meta.id)
        except ImageNotFound:
            logger.warning("Image ID '%s' not found. Skipping.", meta.id)
            return

        logger.info("Backing up image ID '%s'...", meta.id)
        try:
            with open(temp_path, "wb") as raw:
                cctx = zstd.ZstdCompressor(level=ZSTD_COMPRESSION_LEVEL)
                with cctx.stream_writer(raw) as compressor:
                    for chunk in image.save(
                        named=True, chunk_size=DOCKER_SAVE_CHUNK_SIZE
                    ):
                        compressor.write(chunk)
            temp_path.replace(archive_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        logger.info(
            "Backup complete for image ID '%s' (%s).",
            meta.id,
            format_file_path_size(archive_path),
        )
    else:
        logger.info(
            "Archive already exists for image ID '%s' (%s). Skipping.",
            meta.id,
            format_file_path_size(archive_path),
        )

    metadata_path.write_text(meta.model_dump_json(indent=2))


def docker_restore_image(image_id: str, backup_dir: Path) -> None:
    setup_subprocess_logging()
    client = get_docker_client()

    image_dir = backup_dir / image_id
    archive_path = image_dir / "image.tar.zst"
    metadata_path = image_dir / "meta.json"

    if not archive_path.exists() or not metadata_path.exists():
        logger.warning("Missing archive or metadata for '%s'. Skipping.", image_id)
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = ImageMetadata.model_validate_json(f.read())

    try:
        client.images.get(image_id)
        logger.info("Image ID '%s' already loaded. Skipping import.", image_id)
        return
    except ImageNotFound:
        pass
    logger.info(
        "Loading image ID '%s' (%s) from archive...",
        image_id,
        format_file_path_size(archive_path),
    )
    try:
        with open(archive_path, "rb") as raw:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(raw) as reader:
                client.images.load(reader)  # type: ignore
    except ImageLoadError as e:
        logger.warning("Failed to load image ID '%s': %s", image_id, e)
        return

    image = client.images.get(image_id)
    for tag in meta.tags:
        image.tag(tag)
        logger.info("Tagged image ID '%s' as '%s'.", image_id, tag)


# -------------------------------
# CLI Entry Point
# -------------------------------
def cmd_backup(parallel: int, image_dir: Path, pattern: str, prune: bool) -> None:
    image_metadata = get_image_map(pattern)
    logger.info("Found %d unique images to back up.", len(image_metadata))

    # Create the backup directory if it doesn't exist
    logger.info("Creating: %s", image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    if prune:
        kept_dirs = {meta.id for meta in image_metadata}
        for child in image_dir.iterdir():
            if child.name not in kept_dirs:
                logger.info("Pruning: %s", child)
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    shutil.rmtree(child)

    with ProcessPoolExecutor(max_workers=parallel or None) as executor:
        futures = [
            executor.submit(docker_backup_image, meta, image_dir)
            for meta in image_metadata
        ]
        for future in as_completed(futures):
            future.result()

    # Print total size of image_dir directory
    total_size = sum(f.stat().st_size for f in image_dir.glob("**/*") if f.is_file())
    logger.info("Total size of backup: %s", format_size(total_size))


def cmd_restore(
    parallel: int,
    image_dir: Path,
) -> None:
    if not image_dir.is_dir():
        logger.warning("Directory %s does not exist. Nothing to restore.", image_dir)
        return
    image_dirs = [p for p in image_dir.iterdir() if (p / "meta.json").exists()]
    logger.info("Found %d images to restore.", len(image_dirs))
    with ProcessPoolExecutor(max_workers=parallel or None) as executor:
        futures = [
            executor.submit(docker_restore_image, p.name, image_dir) for p in image_dirs
        ]
        for future in as_completed(futures):
            future.result()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup and restore Docker images.")
    parser.add_argument(
        "-m", "--minikube", action="store_true", help="Use Minikube's Docker daemon."
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=os.cpu_count(),
        help="Number of parallel jobs to run (0 = unlimited, default = CPU count).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_b = subparsers.add_parser("backup", help="Backup images by regex.")
    parser_b.add_argument(
        "-p",
        "--prune",
        action="store_true",
        help="Prune outdated backup directories not updated during this run.",
    )
    parser_b.add_argument("pattern", help="Regex to match image names.")
    parser_b.add_argument("directory", type=Path, help="Target backup directory.")

    parser_r = subparsers.add_parser(
        "restore", help="Restore all images from a directory."
    )
    parser_r.add_argument("directory", type=Path, help="Backup source directory.")

    args = parser.parse_args()

    # Arguments
    minikube: bool = args.minikube
    command: str = args.command

    listener.start()
    try:
        if minikube:
            load_minikube_env()

        match command:
            case "backup":
                cmd_backup(args.parallel, args.directory, args.pattern, args.prune)
            case "restore":
                cmd_restore(args.parallel, args.directory)
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
