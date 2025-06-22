#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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

    logger.info("Backup completed.")


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
        "Restoring  volume '%s' to '%s' using image '%s'...",
        volume_name,
        archive_path,
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
        default="alpine",
        help="Docker image to use for backup/restore (default: alpine)",
    )
    args = parser.parse_args()

    backup_dir = Path(args.directory)

    if args.action == "backup":
        backup_volume(args.volume, backup_dir, args.image)
    elif args.action == "restore":
        restore_volume(args.volume, backup_dir, args.image)


if __name__ == "__main__":
    main()
