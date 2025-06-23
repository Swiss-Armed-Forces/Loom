#!/usr/bin/env python3
import argparse
import logging
import os
from pathlib import Path
import docker

CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX = os.environ.get(
    "CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX", ""
)
DEFAULT_IMAGE = "alpine"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def format_file_size(file_path: Path) -> str:
    """
    Get file size and format it with the most appropriate unit (TiB, GiB, MiB, KiB, or bytes).

    Args:
        file_path: Path to the file

    Returns:
        Formatted size string (e.g., "1.23 GiB", "456.78 MiB", "12.34 KiB", "123 bytes")
    """
    if not file_path.exists():
        return "File not found"

    size_bytes = file_path.stat().st_size

    # Define units in descending order
    units = [
        (1024**4, "TiB"),
        (1024**3, "GiB"),
        (1024**2, "MiB"),
        (1024**1, "KiB"),
        (1, "bytes"),
    ]

    for divisor, unit in units:
        if size_bytes >= divisor:
            size = size_bytes / divisor
            if unit == "bytes":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"

    return "0 bytes"


def backup_volume(volume_name: str, backup_dir: Path, image: str):
    """
    Backup a Docker volume to a .tar.gz file in the specified directory using Docker SDK.

    Args:
        volume_name: Name of the Docker volume.
        backup_dir: Path to the directory where the backup will be stored.
        image: Docker image to use for the backup container.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"{volume_name}.tar.gz"
    archive_path = backup_dir / archive_name

    client = docker.from_env()

    logger.info(
        "Backing up volume '%s' to '%s' using image '%s'...",
        volume_name,
        archive_path,
        image,
    )

    container = client.containers.run(
        image=image,
        command=["sh", "-c", f"tar czf /backup/{archive_name} -C /volume ."],
        volumes={
            volume_name: {"bind": "/volume", "mode": "ro"},
            str(backup_dir.resolve()): {"bind": "/backup", "mode": "rw"},
        },
        remove=True,
        detach=True,
    )
    container.wait()

    logger.info("Backup completed. Size: %s", format_file_size(archive_path))


def restore_volume(volume_name: str, backup_dir: Path, image: str):
    """
    Restore a Docker volume from a .tar.gz file in the specified directory using Docker SDK.

    Args:
        volume_name: Name of the Docker volume to restore.
        backup_dir: Path to the directory containing the backup.
        image: Docker image to use for the restore container.
    """
    archive_name = f"{volume_name}.tar.gz"
    archive_path = backup_dir / archive_name

    if not archive_path.exists():
        logger.info("Backup file not found: %s", archive_path)
        return

    logger.info(
        "Restoring  volume '%s' from '%s' (%s) using image '%s'...",
        volume_name,
        archive_path,
        format_file_size(archive_path),
        image,
    )

    client = docker.from_env()

    container = client.containers.run(
        image=image,
        command=["sh", "-c", f"tar xzf /backup/{archive_name} -C /volume"],
        volumes={
            volume_name: {"bind": "/volume", "mode": "rw"},
            str(backup_dir.resolve()): {"bind": "/backup", "mode": "ro"},
        },
        remove=True,
        detach=True,
    )
    container.wait()

    logger.info("Restore completed.")


def main():
    parser = argparse.ArgumentParser(description="Backup and restore Docker volumes.")
    parser.add_argument(
        "action", choices=["backup", "restore"], help="Action to perform."
    )
    parser.add_argument("volume", help="Name of the Docker volume.")
    parser.add_argument("directory", help="Directory to store/read backups.")
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help="Docker image to use for backup/restore (default: alpine)",
    )
    args = parser.parse_args()

    backup_dir = Path(args.directory)
    image = (
        f"{CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/{args.image}"
        if CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
        else args.image
    )

    if args.action == "backup":
        backup_volume(args.volume, backup_dir, image)
    elif args.action == "restore":
        restore_volume(args.volume, backup_dir, image)


if __name__ == "__main__":
    main()
